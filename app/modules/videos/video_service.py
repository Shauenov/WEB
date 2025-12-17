from __future__ import annotations

import os
import uuid
import tempfile
from datetime import datetime, UTC
from typing import Optional, IO

from fastapi import HTTPException, UploadFile, BackgroundTasks
from sqlmodel import Session

from app.core.config import settings
from app.core.s3 import MinioService
from app.models import Video, VideoStatus
from app.modules.videos.video_repository import VideoRepository
from app.modules.videos.videos_transcode_service import VideosTranscodeService


def _guess_ct(name: str, fallback: Optional[str] = None) -> str:
    import mimetypes
    return fallback or mimetypes.guess_type(name)[0] or "application/octet-stream"


def _bucket() -> str:
    b = getattr(settings, "AWS_S3_BUCKET_NAME", None)
    if not b:
        raise RuntimeError("AWS_S3_BUCKET_NAME is not set")
    return b


class VideoService:
    def __init__(self, session: Session):
        self.repo = VideoRepository(session)
        self.session = session
        self.s3 = MinioService()
        self.bucket = _bucket()
        self.hls = VideosTranscodeService()

    # --- helpers ---
    def _ensure(self, vid: str) -> Video:
        v = self.repo.get(vid)
        if not v or v.deleted_at:
            raise HTTPException(404, "Video not found")
        return v

    def _uuid_or_none(self, s: Optional[str]) -> Optional[uuid.UUID]:
        if not s or not str(s).strip():
            return None
        try:
            return uuid.UUID(str(s).strip())
        except ValueError:
            raise HTTPException(status_code=422, detail="genre_id must be a valid UUID")

    def _copy_stream_to_tmp(self, stream: IO[bytes]) -> str:
        """
        Копирует поток (seek'нём в начало, если можно) в temp-файл. Возвращает путь.
        """
        try:
            stream.seek(0)
        except Exception:
            pass
        with tempfile.NamedTemporaryFile(delete=False) as tmp:
            while True:
                chunk = stream.read(1024 * 1024)
                if not chunk:
                    break
                tmp.write(chunk)
            return tmp.name

    def get(self, vid: str) -> Video:
        return self._ensure(vid)

    # --- use cases ---
    def create(
        self,
        title: str,
        description: str,
        preview_upload: UploadFile,
        video_upload: UploadFile,
        genre_id: Optional[str] = None,
        background_tasks: Optional[BackgroundTasks] = None,
    ) -> Video:
        vid = str(uuid.uuid4())

        # ключи
        preview_ext = os.path.splitext(preview_upload.filename or "")[1] or ".jpg"
        source_ext = os.path.splitext(video_upload.filename or "")[1] or ".mp4"
        preview_key = f"videos/{vid}/preview{preview_ext}"
        source_key = f"videos/{vid}/source{source_ext}"

        # 1) Превью → tmp → MinIO
        tmp_prev_path = self._copy_stream_to_tmp(preview_upload.file)
        try:
            self.s3.client.fput_object(
                bucket_name=self.bucket,
                object_name=preview_key,
                file_path=tmp_prev_path,
                content_type=_guess_ct(preview_upload.filename, preview_upload.content_type),
            )
        finally:
            try:
                os.remove(tmp_prev_path)
            except Exception:
                pass

        # 2) Исходник → tmp → MinIO (как source)
        tmp_vid_path = self._copy_stream_to_tmp(video_upload.file)
        self.s3.client.fput_object(
            bucket_name=self.bucket,
            object_name=source_key,
            file_path=tmp_vid_path,
            content_type=_guess_ct(video_upload.filename, video_upload.content_type),
        )

        # 3) Создаём запись в статусе PROCESSING
        v = Video(
            id=vid,
            title=title,
            description=description,
            preview_img=preview_key,
            video=source_key,  # временно (до HLS)
            status=VideoStatus.PROCESSING,
            genre_id=self._uuid_or_none(genre_id),
        )
        v = self.repo.create(v)

        # 4) Фон: HLS → MinIO → обновление записи
        if background_tasks is not None:
            background_tasks.add_task(self._bg_transcode_and_update, vid, tmp_vid_path)
        else:
            self._bg_transcode_and_update(vid, tmp_vid_path)

        return v

    def _bg_transcode_and_update(self, vid: str, tmp_src_path: str) -> None:
        try:
            master_key = self.hls.transcode_and_upload(vid=vid, src_path=tmp_src_path)
            v = self._ensure(vid)
            v.video = master_key
            v.status = VideoStatus.ACTIVE
            v.updated_at = datetime.now(UTC)
            self.repo.save(v)
        except Exception:
            try:
                v = self._ensure(vid)
                v.status = VideoStatus.FAILED
                v.updated_at = datetime.now(UTC)
                self.repo.save(v)
            except Exception:
                pass
        finally:
            try:
                os.remove(tmp_src_path)
            except Exception:
                pass

    def list(self, status, q, limit: int, offset: int):
        return self.repo.list(status=status, q=q, limit=limit, offset=offset)

    def patch(
        self,
        vid: str,
        *,
        title: Optional[str] = None,
        description: Optional[str] = None,
        status: Optional[VideoStatus] = None,
        genre_id: Optional[str] = None,
    ) -> Video:
        v = self._ensure(vid)

        if title is not None and title != "":
            v.title = title
        if description is not None and description != "":
            v.description = description
        if status is not None:
            v.status = status
        if genre_id is not None:  # пришла строка ("" -> None)
            v.genre_id = self._uuid_or_none(genre_id)

        v.updated_at = datetime.now(UTC)
        return self.repo.save(v)

    def replace_file(self, vid: str, *, fileobj, filename: str, content_type: Optional[str]) -> Video:
        v = self._ensure(vid)
        if v.status == VideoStatus.ARCHIVED:
            raise HTTPException(400, "Archived video cannot be modified")

        ext = os.path.splitext(filename)[1] or ".mp4"
        new_key = f"videos/{vid}/source{ext}"

        # грузим новый исходник
        with tempfile.NamedTemporaryFile(delete=False) as tmp:
            while True:
                chunk = fileobj.read(1024 * 1024)
                if not chunk:
                    break
                tmp.write(chunk)
            tmp_path = tmp.name
        try:
            self.s3.client.fput_object(
                bucket_name=self.bucket,
                object_name=new_key,
                file_path=tmp_path,
                content_type=_guess_ct(filename, content_type),
            )
        finally:
            try:
                os.remove(tmp_path)
            except Exception:
                pass

        v.video = new_key
        v.updated_at = datetime.now(UTC)
        return self.repo.save(v)

    def archive(self, vid: str) -> Video:
        v = self._ensure(vid)
        v.status = VideoStatus.ARCHIVED
        v.updated_at = datetime.now(UTC)
        return self.repo.save(v)

    def restore(self, vid: str) -> Video:
        v = self._ensure(vid)
        v.status = VideoStatus.ACTIVE
        v.updated_at = datetime.now(UTC)
        return self.repo.save(v)

    def soft_delete(self, vid: str) -> dict:
        v = self._ensure(vid)
        v.deleted_at = datetime.now(UTC)
        v.updated_at = v.deleted_at
        self.repo.save(v)
        return {"deleted": vid}

    def play_links(self, vid: str) -> dict:
        v = self._ensure(vid)
        if v.status != VideoStatus.ACTIVE:
            raise HTTPException(404, "Video not ready")

        try:
            self.s3.client.stat_object(self.bucket, v.video)
        except Exception:
            raise HTTPException(410, "Video file missing from storage")

        playlist = self.s3.presign_hls_playlist(v.video, bucket=self.bucket, expires_seconds=3600)
        return {
            "video_url": self.s3.presign_get(v.video, bucket=self.bucket, expires_seconds=3600),
            "playlist": playlist,
            "preview_url": self.s3.presign_get(v.preview_img, bucket=self.bucket, expires_seconds=3600),
            "status": v.status,
        }

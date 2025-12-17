import json
import mimetypes
import tempfile
import uuid
from pathlib import Path
import subprocess
import shutil
from fastapi import HTTPException, UploadFile, BackgroundTasks
from app.models import MusicStatus
from app.core.logger import logger
from app.modules.genre.genre_service import GenreService
from app.schemas import CreateMusic, UpdateMusic, MusicPublic
from app.modules.music.music_repository import MusicRepository
from app.modules.playlist.playlist_service import PlaylistService
from app.core.config import settings
from app.core.s3 import MinioService
from app.modules.transcoder.transcoder_service import TranscoderService

class MusicService():
    def __init__(self):
        self.minio = MinioService()
        self.repo = MusicRepository()
        self.transcoder = TranscoderService()
        self.playlistService = PlaylistService()
        self.genreService = GenreService()

    def _upload_hls_dir(self, local_dir: Path, music_id: str) -> str:
        prefix = f"music/hls/{music_id}/"
        count = 0
        for p in local_dir.glob("*"):
            if p.is_file():
                key = f"{prefix}{p.name}"
                ctype, _ = mimetypes.guess_type(p.name)
                self.minio.client.fput_object(
                    bucket_name=settings.AWS_S3_BUCKET_NAME,
                    object_name=key,
                    file_path=str(p),
                    content_type=ctype or "application/octet-stream",
                )
                count += 1
        if count == 0:
            raise RuntimeError("No HLS files to upload")
        return f"{settings.AWS_S3_PUBLIC_URL}/{settings.AWS_S3_BUCKET_NAME}/{prefix}index.m3u8"

    def transcodeMusic(self, music_id, input_path: str):
        tmp_dir = Path(tempfile.mkdtemp(prefix="hls_music_"))
        output_path = tmp_dir / "index.m3u8"
        try:
            status = self.transcoder.transcodeToHls(input_path, str(output_path))
            if status:
                master_url = self._upload_hls_dir(tmp_dir, music_id)
                self.updateById(music_id, UpdateMusic(status=MusicStatus.ACTIVE, music_url=master_url))
            else:
                self.updateById(music_id, UpdateMusic(status=MusicStatus.FAILED))
        finally:
            try:
                Path(input_path).unlink(missing_ok=True)
            except Exception:
                pass
            try:
                shutil.rmtree(tmp_dir, ignore_errors=True)
            except Exception:
                pass

    async def create(
        self,
        playlist_id: str,
        title: str,
        description: str,
        preview_img: UploadFile,
        music: UploadFile,
        background_tasks: BackgroundTasks,
        genre_id: str | None = None,
    ) -> MusicPublic:
        try:
            playlist = self.playlistService.findById(playlist_id)
            if not playlist:
                raise HTTPException(status_code=400, detail="Playlist not found")

            genre = None
            if genre_id:
                genre = self.genreService.get_by_id(genre_id)
                if not genre:
                    raise HTTPException(status_code=400, detail="Genre not found")

            self.validate_audio_file(music)
            with tempfile.NamedTemporaryFile(delete=False) as tmp:
                image_tmp_path = tmp.name
                tmp.write(await preview_img.read())

            mime_type, _ = mimetypes.guess_type(preview_img.filename)
            ext = mimetypes.guess_extension(mime_type) or ".jpg"
            object_name = f"{uuid.uuid4()}{ext}"
            image_key = self.minio.upload_file(object_name, image_tmp_path, settings.AWS_S3_BUCKET_NAME)

            with tempfile.NamedTemporaryFile(delete=False) as tmp:
                music_tmp_path = tmp.name
                tmp.write(await music.read())

            mime_type, _ = mimetypes.guess_type(music.filename)
            ext = mimetypes.guess_extension(mime_type) or ".mp3"
            object_name = f"{uuid.uuid4()}{ext}"
            music_key = self.minio.upload_file(object_name, music_tmp_path, settings.AWS_S3_BUCKET_NAME)

            duration = self.get_audio_duration(music_tmp_path)

            music_obj = self.repo.create(
                CreateMusic(
                    playlist_id=playlist_id,
                    title=title,
                    description=description,
                    duration=duration,
                    music_url=music_key,
                    preview_img=image_key,
                    genre_id=genre_id if genre else None,
                )
            )

            background_tasks.add_task(self.transcodeMusic, music_obj.id, music_tmp_path)

            return music_obj
        except HTTPException as e:
            raise e
        except Exception as e:
            logger.error("error %s", e)
            raise HTTPException(status_code=500, detail="Internal server error")

    def findById(self, id: str) -> MusicPublic | None:
        try:
            music = self.repo.findById(id)
            if not music:
                raise HTTPException(status_code=404, detail="Music not found")
            return music
        except HTTPException:
            raise
        except Exception as e:
            logger.error("error %s", e)
            raise HTTPException(status_code=500)

    def findAll(self, skip: int | None = None, limit: int | None = None, q: str | None = None, playlist_id: uuid.UUID | None = None) -> list[MusicPublic]:
        try:
            musics = self.repo.findAll(skip, limit, q, playlist_id)
            return musics
        except Exception as e:
            logger.error("error %s", e)
            raise HTTPException(status_code=500)

    def updateById(self, id: str, data: UpdateMusic) -> MusicPublic:
        try:
            music = self.repo.updateById(id, data)
            if not music:
                raise HTTPException(status_code=404, detail="Music not found")
            return music
        except HTTPException:
            raise
        except Exception as e:
            logger.error("%s", e)
            raise HTTPException(status_code=500)

    def deleteById(self, id: str) -> MusicPublic | None:
        try:
            music = self.repo.deleteById(id)
            if not music:
                raise HTTPException(status_code=404, detail="Music not found")
            return music
        except HTTPException:
            raise
        except Exception as e:
            logger.error("%s", e)
            raise HTTPException(status_code=500)

    def _extract_key(self, url_or_key: str) -> str:
        bucket = settings.AWS_S3_BUCKET_NAME
        marker = f"/{bucket}/"
        if marker in url_or_key:
            return url_or_key.split(marker, 1)[1]
        return url_or_key.lstrip("/")

    def presigned_links(self, id: str) -> dict:
        music = self.findById(id)
        if not music:
            raise HTTPException(status_code=404, detail="Music not found")

        def presign_if_exists(key: str) -> str | None:
            try:
                self.minio.client.stat_object(settings.AWS_S3_BUCKET_NAME, key)
                return self.minio.presign_get(key, bucket=settings.AWS_S3_BUCKET_NAME, expires_seconds=3600)
            except Exception:
                return None

        links = {}
        if music.music_url:
            key = self._extract_key(music.music_url)
            link = presign_if_exists(key)
            if not link:
                fallback_key = f"music/hls/{id}/index.m3u8"
                link = presign_if_exists(fallback_key)
                key = fallback_key
            if not link:
                raise HTTPException(status_code=404, detail="Music file missing from storage")
            if key.endswith(".m3u8"):
                links["playlist"] = self.minio.presign_hls_playlist(key, bucket=settings.AWS_S3_BUCKET_NAME, expires_seconds=3600)
            links["music_url"] = link
        if music.preview_img:
            key = self._extract_key(music.preview_img)
            link = presign_if_exists(key)
            if link:
                links["preview_img"] = link
        return links


    def validate_audio_file(self, file: UploadFile):
        ALLOWED_AUDIO_TYPES = {
            "audio/mpeg",
            "audio/wav",
            "audio/ogg",
            "audio/x-flac",
            "audio/mp4",
            "audio/vnd.wave",
            "video/webm",
        }

        if file.content_type not in ALLOWED_AUDIO_TYPES:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid audio file type: {file.content_type}"
            )

        ext = file.filename.split(".")[-1].lower()
        if ext not in {"mp3", "wav", "ogg", "flac", "m4a", "webm"}:
            raise HTTPException(
                status_code=400,
                detail=f"Unsupported file extension: .{ext}"
            )
        
    def get_audio_duration(self, path: str) -> int:
        result = subprocess.run(
            ["ffprobe", "-v", "quiet", "-print_format", "json", "-show_format", path],
            capture_output=True,
            text=True
        )
        info = json.loads(result.stdout)
        return int(float(info["format"]["duration"]))

import tempfile
import uuid
from pathlib import Path
from fastapi import BackgroundTasks, HTTPException, UploadFile

import mimetypes
import os
import shutil
from app.models import Ad, AdStatus
from app.core.logger import logger
from app.core.config import settings
from app.core.s3 import MinioService
from app.schemas import CreateAd, UpdateAd, AdPublic
from app.modules.ads.ads_repository import AdRepository
from app.modules.transcoder.transcoder_service import TranscoderService

VALID_VIDEO_TYPES = {"video/mp4", "video/avi", "video/mpeg", "video/quicktime", "video/webm"}

class AdService():
    def __init__(self):
        self.minio = MinioService()
        self.repo = AdRepository()
        self.transcoder = TranscoderService()

    def _upload_hls_dir(self, local_dir: Path, ad_id: str) -> str:
        prefix = f"ads/hls/{ad_id}/"
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

    def transcodeAd(self, ad_id, input_path: str):
        tmp_dir = Path(tempfile.mkdtemp(prefix="hls_ad_"))
        output_path = tmp_dir / "index.m3u8"
        try:
            status = self.transcoder.transcodeToHls(input_path, str(output_path))
            if status:
                master_url = self._upload_hls_dir(tmp_dir, ad_id)
                self.updateById(ad_id, UpdateAd(status=AdStatus.ACTIVE, video_url=master_url))
            else:
                self.updateById(ad_id, UpdateAd(status=AdStatus.FAILED))
        finally:
            try:
                Path(input_path).unlink(missing_ok=True)
            except Exception:
                pass
            try:
                shutil.rmtree(tmp_dir, ignore_errors=True)
            except Exception:
                pass

    async def create(self, data: CreateAd, ad: UploadFile, background_tasks: BackgroundTasks) -> AdPublic:
        try:
            self.validate_file(ad, VALID_VIDEO_TYPES, "ad")

            with tempfile.NamedTemporaryFile(delete=False) as tmp:
                tmp_path = tmp.name
                tmp.write(await ad.read())
            ad_ext = mimetypes.guess_extension(ad.content_type) or os.path.splitext(ad.filename)[1]
            object_name = f"{uuid.uuid4()}{ad_ext}"
            ad_key = self.minio.upload_file(object_name, tmp_path, settings.AWS_S3_BUCKET_NAME)

            ad_obj = self.repo.create(
                Ad(
                    title=data.title,
                    video_url=ad_key,
                    status=AdStatus.PROCESSING
                )
            )

            background_tasks.add_task(self.transcodeAd, ad_obj.id, tmp_path)

            return ad_obj
        except HTTPException as e:
            raise e
        except Exception as e:
            logger.error("error %s", e)
            raise HTTPException(status_code=500, detail="Internal server error")

    def findById(self, id: str) -> AdPublic | None:
        try:
            ad = self.repo.findById(id)
            if not ad:
                raise HTTPException(status_code=404, detail="Ad not found")
            return ad
        except HTTPException:
            raise
        except Exception as e:
            logger.error("error %s", e)
            raise HTTPException(status_code=500)

    def findAll(self, skip: int | None = None, limit: int | None = None, order_by: str = "date", q: str | None = None) -> list[AdPublic]:
        try:
            ads = self.repo.findAll(skip, limit, order_by, q=q)
            return ads
        except Exception as e:
            logger.error("error %s", e)
            raise HTTPException(status_code=500)

    def updateById(self, id: str, data: UpdateAd) -> AdPublic:
        try:
            ad = self.repo.updateById(id, data)
            if not ad:
                raise HTTPException(status_code=404, detail="Ad not found")
            return ad
        except HTTPException:
            raise
        except Exception as e:
            logger.error("%s", e)
            raise HTTPException(status_code=500)

    def deleteById(self, id: str) -> AdPublic | None:
        try:
            ad = self.repo.deleteById(id)
            if not ad:
                raise HTTPException(status_code=404, detail="Ad not found")
            return ad
        except HTTPException:
            raise
        except Exception as e:
            logger.error("%s", e)
            raise HTTPException(status_code=500)


    def validate_file(self, upload: UploadFile, allowed_types: set[str], kind: str):
        if upload.content_type not in allowed_types:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid {kind} type: {upload.content_type}. Allowed: {', '.join(allowed_types)}"
            )

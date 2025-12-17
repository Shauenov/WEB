import json
import mimetypes
import os
import tempfile
from typing import Optional
from datetime import timedelta
from urllib.parse import urlparse
from fastapi import UploadFile
from minio import Minio
from minio.error import S3Error
from app.core.logger import logger
from app.core.config import settings

class MinioService:
    def __init__(self):
        # если endpoint начинается с https:// — включим secure=True
        endpoint = settings.AWS_S3_ENDPOINT_URL.replace("https://", "").replace("http://", "")
        secure = settings.AWS_S3_ENDPOINT_URL.startswith("https://") or getattr(settings, "AWS_S3_SECURE", False)

        self.client = Minio(
            endpoint=endpoint,
            access_key=settings.AWS_ACCESS_KEY_ID,
            secret_key=settings.AWS_SECRET_ACCESS_KEY,
            region=getattr(settings, "AWS_REGION", None),
            secure=secure,
        )

    def ensure_bucket(self, bucket: str, public_read: bool = False) -> None:
        try:
            if not self.client.bucket_exists(bucket):
                self.client.make_bucket(bucket)
                if public_read:
                    policy = {
                        "Version": "2012-10-17",
                        "Statement": [{
                            "Action": ["s3:GetObject"],
                            "Effect": "Allow",
                            "Principal": {"AWS": ["*"]},
                            "Resource": [f"arn:aws:s3:::{bucket}/*"],
                        }],
                    }
                    self.client.set_bucket_policy(bucket, json.dumps(policy))
        except S3Error as e:
            logger.error("ensure_bucket error: %s", e)
            raise

    def upload_file(self, object_name: str, src_path: str, bucket: str, content_type: Optional[str] = None) -> str:
        """Загружает локальный файл в MinIO. Возвращает ключ вида '{bucket}/{object_name}'."""
        try:
            self.ensure_bucket(bucket, public_read=False)
            self.client.fput_object(
                bucket_name=bucket,
                object_name=object_name,
                file_path=src_path,
                content_type=content_type,
            )
            logger.info("uploaded %s to s3://%s/%s", src_path, bucket, object_name)
            return f"{settings.AWS_S3_PUBLIC_URL}/{bucket}/{object_name}"
        except S3Error as e:
            logger.error("upload_file error: %s", e)
            raise

    def delete_object(self, object_name: str, bucket: str) -> None:
        try:
            self.client.remove_object(bucket, object_name)
        except S3Error as e:
            logger.error("delete_object error: %s", e)
            raise

    def presign_get(self, object_name: str, bucket: str, expires_seconds: int = 3600) -> str:
        """Выдаёт временную ссылку на скачивание (рекомендуется вместо public-policy)."""
        try:
            expires = expires_seconds if hasattr(expires_seconds, "total_seconds") else timedelta(seconds=expires_seconds)
            presign_endpoint = settings.AWS_S3_PUBLIC_URL or settings.AWS_S3_ENDPOINT_URL
            if "://" not in presign_endpoint:
                presign_endpoint = f"http://{presign_endpoint}"
            parsed = urlparse(presign_endpoint)
            endpoint = parsed.netloc or parsed.path
            secure = parsed.scheme == "https"
            presign_client = Minio(
                endpoint=endpoint,
                access_key=settings.AWS_ACCESS_KEY_ID,
                secret_key=settings.AWS_SECRET_ACCESS_KEY,
                region=getattr(settings, "AWS_REGION", None),
                secure=secure,
            )
            return presign_client.presigned_get_object(bucket, object_name, expires=expires)
        except S3Error as e:
            logger.error("presign_get error: %s", e)
            raise

    def presign_hls_playlist(self, object_name: str, bucket: str, expires_seconds: int = 3600) -> str:
        """Generate HLS playlist with presigned segment URLs."""
        response = None
        try:
            response = self.client.get_object(bucket, object_name)
            raw = response.read().decode("utf-8")
            prefix = object_name.rsplit("/", 1)[0] + "/" if "/" in object_name else ""
            lines = []
            for line in raw.splitlines():
                stripped = line.strip()
                if not stripped or stripped.startswith("#"):
                    lines.append(line)
                    continue
                if stripped.startswith("http://") or stripped.startswith("https://"):
                    lines.append(stripped)
                    continue
                seg_key = f"{prefix}{stripped}"
                seg_url = self.presign_get(seg_key, bucket=bucket, expires_seconds=expires_seconds)
                lines.append(seg_url)
            return "\n".join(lines) + "\n"
        except Exception as e:
            logger.error("presign_hls_playlist error: %s", e)
            raise
        finally:
            if response is not None:
                try:
                    response.close()
                    response.release_conn()
                except Exception:
                    pass

    def upload_uploadfile(
        self,
        object_name: str,
        file: UploadFile,
        bucket: str,
        content_type: Optional[str] = None,
    ) -> str:
        """
        Принимает UploadFile, сохраняет во временный файл и загружает в MinIO.
        Возвращает публичный URL (как и upload_file).
        """
        # выберем content-type максимально аккуратно
        ctype = content_type or file.content_type or mimetypes.guess_type(file.filename or "")[0] or "application/octet-stream"

        # читаем буфер и пишем во временный файл
        with tempfile.NamedTemporaryFile(delete=False) as tmp:
            # важно: используем file.file.read(), чтобы не путаться с async/await
            data = file.file.read()
            tmp.write(data)
            tmp_path = tmp.name

        try:
            return self.upload_file(object_name, tmp_path, bucket, content_type=ctype)
        finally:
            try:
                os.remove(tmp_path)
            except Exception:
                pass

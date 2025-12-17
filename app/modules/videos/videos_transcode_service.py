from __future__ import annotations
import os
import shutil
import tempfile
from pathlib import Path
from typing import List, Tuple

from app.core.logger import logger
from app.core.config import settings
from app.core.s3 import MinioService
from app.modules.transcoder.transcoder_service import TranscoderService  # используем менторский

class VideosTranscodeService:
    """
    Обёртка для HLS под /videos:
    - кладёт выход ffmpeg во временную папку
    - загружает ВСЕ файлы HLS в MinIO под hls/videos/{vid}/...
    - возвращает (master_key, uploaded_files_count)
    """
    def __init__(self):
        self.minio = MinioService()
        self.bucket = settings.AWS_S3_BUCKET_NAME
        self.t = TranscoderService()

    def _mk_tmpdir(self) -> str:
        return tempfile.mkdtemp(prefix="hls_")

    def _cleanup(self, *paths: str) -> None:
        for p in paths:
            try:
                if os.path.isdir(p):
                    shutil.rmtree(p, ignore_errors=True)
                elif os.path.exists(p):
                    os.remove(p)
            except Exception:
                pass

    def _upload_dir(self, local_dir: str, dest_prefix: str) -> int:
        base = Path(local_dir)
        count = 0
        for p in base.glob("*"):
            # загружаем только файлы верхнего уровня (m3u8 и ts)
            if p.is_file():
                key = f"{dest_prefix}{p.name}"
                self.minio.client.fput_object(
                    bucket_name=self.bucket,
                    object_name=key,
                    file_path=str(p),
                    content_type=_guess_ct_by_name(p.name),
                )
                count += 1
        return count

    def transcode_and_upload(self, *, vid: str, src_path: str) -> str:
        """
        Делает single-variant HLS (как в ads, без лестницы).
        Возвращает ключ мастер-плейлиста в MinIO: hls/videos/{vid}/index.m3u8
        """
        out_dir = self._mk_tmpdir()
        master_local = os.path.join(out_dir, "index.m3u8")

        try:
            ok = self.t.transcodeToHls(input_path=src_path, output_path=master_local)
            if not ok:
                raise RuntimeError("ffmpeg failed")

            dest_prefix = f"hls/videos/{vid}/"
            uploaded = self._upload_dir(out_dir, dest_prefix)
            if uploaded == 0:
                raise RuntimeError("no files uploaded")

            master_key = f"{dest_prefix}index.m3u8"
            return master_key
        finally:
            self._cleanup(out_dir)

    
    
def _guess_ct_by_name(name: str) -> str:
    import mimetypes
    return mimetypes.guess_type(name)[0] or "application/octet-stream"




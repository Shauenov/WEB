import mimetypes
import os
import tempfile
import uuid
from fastapi import HTTPException, UploadFile
from app.core.logger import logger
from app.schemas import CreatePlaylist, UpdatePlaylist, PlaylistPublic
from app.modules.playlist.playlist_repository import PlaylistRepository
from app.core.config import settings
from app.core.s3 import MinioService

class PlaylistService():
    def __init__(self):
        self.repo = PlaylistRepository()
        self.minio = MinioService()

    async def create(self, title: str, description: str, preview_img: UploadFile) -> PlaylistPublic:
        try:
            with tempfile.NamedTemporaryFile(delete=False) as tmp:
                image_tmp_path = tmp.name
                tmp.write(await preview_img.read())

            image_ext = mimetypes.guess_extension(preview_img.content_type) or os.path.splitext(preview_img.filename)[1]
            object_name = f"{uuid.uuid4()}{image_ext}"
            image_key = self.minio.upload_file(object_name, image_tmp_path, settings.AWS_S3_BUCKET_NAME)

            return self.repo.create(CreatePlaylist(title=title, description=description, preview_img=image_key))
        except HTTPException as e:
            raise e
        except Exception as e:
            logger.error("error %s", e)
            raise HTTPException(status_code=500, detail="Internal server error")

    def findById(self, id: str) -> PlaylistPublic | None:
        try:
            playlist = self.repo.findById(id)
            if not playlist:
                raise HTTPException(status_code=404, detail="Playlist not found")
            return playlist
        except HTTPException:
            raise
        except Exception as e:
            logger.error("error %s", e)
            raise HTTPException(status_code=500)

    def findAll(self, skip: int | None = None, limit: int | None = None, q: str | None = None) -> list[PlaylistPublic]:
        try:
            playlists = self.repo.findAll(skip, limit, q)
            return playlists
        except Exception as e:
            logger.error("error %s", e)
            raise HTTPException(status_code=500)

    def updateById(self, id: str, data: UpdatePlaylist) -> PlaylistPublic:
        try:
            playlist = self.repo.updateById(id, data)
            if not playlist:
                raise HTTPException(status_code=404, detail="Playlist not found")
            return playlist
        except HTTPException:
            raise
        except Exception as e:
            logger.error("%s", e)
            raise HTTPException(status_code=500)

    def deleteById(self, id: str) -> PlaylistPublic | None:
        try:
            playlist = self.repo.deleteById(id)
            if not playlist:
                raise HTTPException(status_code=404, detail="Playlist not found")
            return playlist
        except HTTPException:
            raise
        except Exception as e:
            logger.error("%s", e)
            raise HTTPException(status_code=500)

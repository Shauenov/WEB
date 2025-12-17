import uuid
from typing import Annotated
from fastapi import APIRouter, Form, Path, UploadFile, Depends
from pydantic import Field

from app.schemas import PlaylistPublic
from app.modules.playlist.playlist_service import PlaylistService
from app.modules.auth.auth_router import any_user_guard, admin_guard

service = PlaylistService()

playlist_router = APIRouter(
    prefix="/playlists",
    tags=["Playlist"],
)

@playlist_router.get("/{id}", response_model=PlaylistPublic | None)
def get_playlist_by_id(
    id: Annotated[str, Path(description="The id of playlist")],
    _=Depends(any_user_guard),
):
    return service.findById(id)

@playlist_router.get("/", response_model=list[PlaylistPublic])
def get_playlists(
    skip: int | None = None,
    limit: int | None = None,
    q: str | None = None,
    _=Depends(any_user_guard),
):
    return service.findAll(skip=skip, limit=limit, q=q)

@playlist_router.post("/", response_model=PlaylistPublic)
async def create_playlist(
    title: Annotated[
        str,
        Form(...),
        Field()
    ],
    description: Annotated[
        str,
        Form(...),
        Field()
    ],
    preview_img: UploadFile,
    _=Depends(admin_guard),
):
    return await service.create(title=title, description=description, preview_img=preview_img)

@playlist_router.delete("/{id}", response_model=PlaylistPublic)
def delete_playlist(
    id: Annotated[uuid.UUID, Path(description="The id of playlist")],
    _=Depends(admin_guard),
):
    return service.deleteById(id)

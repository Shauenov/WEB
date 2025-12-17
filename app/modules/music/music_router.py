import uuid
from typing import Annotated
from fastapi import APIRouter, BackgroundTasks, Form, Path, UploadFile, Depends
from pydantic import Field

from app.schemas import MusicPublic, UpdateMusic
from app.modules.music.music_service import MusicService
from app.modules.auth.auth_router import any_user_guard, admin_guard

service = MusicService()

music_router = APIRouter(
    prefix="/musics",
    tags=["Music"],
)

@music_router.get("/{id}", response_model=MusicPublic | None)
def get_music_by_id(
    id: Annotated[str, Path(description="The id of music")],
    _=Depends(any_user_guard),
):
    return service.findById(id)

@music_router.get("/", response_model=list[MusicPublic])
def get_musics(
    skip: int | None = None,
    limit: int | None = None,
    q: str | None = None,
    playlist_id: uuid.UUID | None = None,
    _=Depends(any_user_guard),
):
    return service.findAll(skip=skip, limit=limit, q=q, playlist_id=playlist_id)

@music_router.post("/", response_model=MusicPublic)
async def create_music(
    playlist_id: Annotated[
        uuid.UUID,
        Form(...),
        Field()
    ],
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
    music: UploadFile,
    background_tasks: BackgroundTasks,
    genre_id: Annotated[str | None, Form(...)] = None,
    _=Depends(admin_guard),
):
    return await service.create(
        playlist_id=str(playlist_id),
        title=title,
        description=description,
        genre_id=str(genre_id) if genre_id else None,
        preview_img=preview_img,
        music=music,
        background_tasks=background_tasks
    )

@music_router.delete("/{id}", response_model=MusicPublic)
def delete_music(
    id: Annotated[uuid.UUID, Path(description="The id of music")],
    _=Depends(admin_guard),
):
    return service.deleteById(id)

@music_router.patch("/{id}", response_model=MusicPublic)
def update_music(
    id: Annotated[uuid.UUID, Path(description="The id of music")],
    data: UpdateMusic,
    _=Depends(admin_guard),
):
    return service.updateById(str(id), data)

@music_router.patch("/{id}/media", response_model=MusicPublic)
async def update_music_media(
    id: Annotated[uuid.UUID, Path(description="The id of music")],
    background_tasks: BackgroundTasks,
    playlist_id: Annotated[uuid.UUID | None, Form()] = None,
    title: Annotated[str | None, Form()] = None,
    description: Annotated[str | None, Form()] = None,
    genre_id: Annotated[uuid.UUID | None, Form()] = None,
    preview_img: UploadFile | None = None,
    music: UploadFile | None = None,
    _=Depends(admin_guard),
):
    return await service.update_media(
        music_id=str(id),
        playlist_id=playlist_id,
        title=title,
        description=description,
        genre_id=genre_id,
        preview_img=preview_img,
        music=music,
        background_tasks=background_tasks,
    )


@music_router.get("/{id}/links", response_model=dict, dependencies=[Depends(any_user_guard)])
def music_links(
    id: Annotated[str, Path(description="The id of music")],
):
    return service.presigned_links(id)

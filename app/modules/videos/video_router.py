from __future__ import annotations
from typing import List, Optional
from fastapi import APIRouter, Depends, File, Form, HTTPException, Query, UploadFile, BackgroundTasks
from sqlmodel import Session

from app.core.db import get_session
from app.models import VideoStatus
from app.modules.auth.auth_router import admin_guard, any_user_guard
from app.modules.videos.video_service import VideoService
from app.utils.utils_media import is_image_stream
from app.schemas import VideoOut

router = APIRouter()

def svc(session: Session = Depends(get_session)) -> VideoService:
    return VideoService(session)

@router.post("", response_model=VideoOut, dependencies=[Depends(admin_guard)])
async def create_video(
    title: str = Form(...),
    description: str = Form(...),
    preview: UploadFile = File(..., description="preview image"),
    file: UploadFile = File(..., description="video file"),
    genre_id: Optional[str] = Form(None, description="genre UUID"),
    service: VideoService = Depends(svc),
    background_tasks: BackgroundTasks = None,  # просто параметр, НЕ Depends
):
    if not (file.content_type or "").startswith("video/"):
        raise HTTPException(400, "file must be a video/*")
    if not is_image_stream(preview.file, preview.content_type):
        raise HTTPException(400, "preview must be a real image (jpg/png/webp/gif)")

    return service.create(
        title=title,
        description=description,
        preview_upload=preview,
        video_upload=file,
        genre_id=genre_id,
        background_tasks=background_tasks,
    )

@router.get("", response_model=List[VideoOut], dependencies=[Depends(any_user_guard)])
def list_videos(
    status: Optional[VideoStatus] = Query(default=None),
    q: Optional[str] = Query(default=None, description="substring in title/description"),
    limit: int = 50,
    offset: int = 0,
    service: VideoService = Depends(svc),
):
    return service.list(status=status, q=q, limit=limit, offset=offset)

@router.get("/{vid}", response_model=VideoOut, dependencies=[Depends(any_user_guard)])
def get_video(
    vid: str,
    service: VideoService = Depends(svc),
):
    return service.get(vid)


@router.get("/{vid}/play", dependencies=[Depends(any_user_guard)])
def play_video(
    vid: str,
    service: VideoService = Depends(svc),
):
    return service.play_links(vid)

@router.patch("/{vid}", response_model=VideoOut, dependencies=[Depends(admin_guard)])
async def patch_video(
    vid: str,
    title: str = Form(""),
    description: str = Form(""),
    status: Optional[VideoStatus] = Form(None, description="Active | Archived"),
    genre_id: Optional[str] = Form(None, description="genre UUID"),
    service: VideoService = Depends(svc),
):
    return service.patch(
        vid,
        title=title,
        description=description,
        status=status,
        genre_id=genre_id,  # строка или None/"" -> сервис сам разберёт
    )

@router.post("/{vid}/archive", response_model=VideoOut, dependencies=[Depends(admin_guard)])
def archive_video(vid: str, service: VideoService = Depends(svc)):
    return service.archive(vid)

@router.post("/{vid}/restore", response_model=VideoOut, dependencies=[Depends(admin_guard)])
def restore_video(vid: str, service: VideoService = Depends(svc)):
    return service.restore(vid)

@router.delete("/{vid}", response_model=dict, dependencies=[Depends(admin_guard)])
def soft_delete_video(vid: str, service: VideoService = Depends(svc)):
    return service.soft_delete(vid)

# app/schemas.py
from __future__ import annotations

import uuid
from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, Field

# единственный источник enum'ов
from app.models import VideoStatus, AdStatus, GenreType

PHONE_RE = r"^\+7\d{10}$"

# ───────────── Users ─────────────
class CreateUser(BaseModel):
    fullname: str = Field(min_length=2)
    phone: str = Field(pattern=PHONE_RE)
    password: str = Field(min_length=8)
    role: Optional[str] = "user"

class UpdateUser(BaseModel):
    fullname: Optional[str] = Field(default=None, min_length=2)
    phone: Optional[str] = Field(default=None, pattern=PHONE_RE)
    password: Optional[str] = Field(default=None, min_length=8)
    role: Optional[str] = None

class UserPublic(BaseModel):
    id: uuid.UUID
    fullname: str
    phone: str
    role: str

    class Config:
        from_attributes = True


# ───────────── Music / Playlist ─────────────
class CreatePlaylist(BaseModel):
    title: str
    description: str
    # В API мы принимаем файл через UploadFile; это поле — то, что будет храниться (URL/ключ).
    preview_img: str

class UpdatePlaylist(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None

class CreateMusic(BaseModel):
    title: str
    playlist_id: uuid.UUID
    description: str
    # Аналогично: в API загрузка файлом, в БД храним строку-ключ/URL.
    preview_img: str
    music_url: str
    duration: int
    genre_id: Optional[uuid.UUID] = None

class UpdateMusic(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    music_url: Optional[str] = None
    preview_img: Optional[str] = None
    duration: Optional[int] = None
    genre_id: Optional[uuid.UUID] = None
    playlist_id: Optional[uuid.UUID] = None

class MusicPublic(BaseModel):
    id: uuid.UUID
    playlist_id: uuid.UUID
    title: str
    description: str
    preview_img: str
    music_url: str
    duration: int
    genre_id: Optional[uuid.UUID] = None
    created_at: datetime
    updated_at: datetime
    deleted_at: Optional[datetime] = None

    class Config:
        from_attributes = True

class PlaylistPublic(BaseModel):
    id: uuid.UUID
    title: str
    description: str
    preview_img: str
    musics: List["MusicPublic"] = Field(default_factory=list)
    created_at: datetime
    updated_at: datetime
    deleted_at: Optional[datetime] = None

    class Config:
        from_attributes = True


# ───────────── Genres ─────────────
class GenreBase(BaseModel):
    name: str = Field(max_length=100)
    description: Optional[str] = None
    type: GenreType

class GenreCreate(GenreBase):
    pass

class GenreUpdate(BaseModel):
    name: Optional[str] = Field(default=None, max_length=100)
    description: Optional[str] = None
    type: Optional[GenreType] = None

class GenrePublic(BaseModel):
    id: uuid.UUID
    name: str
    description: Optional[str] = None
    type: GenreType
    created_at: datetime
    updated_at: datetime
    deleted_at: Optional[datetime] = None

    class Config:
        from_attributes = True


# ───────────── Ads ─────────────
class CreateAd(BaseModel):
    title: str

class UpdateAd(BaseModel):
    title: Optional[str] = None
    status: Optional[AdStatus] = None
    video_url: Optional[str] = None

class AdPublic(BaseModel):
    id: uuid.UUID
    title: str
    video_url: str
    status: AdStatus
    created_at: datetime
    updated_at: datetime
    deleted_at: Optional[datetime] = None

    class Config:
        from_attributes = True


# ───────────── Videos ─────────────
class VideoCreate(BaseModel):
    title: str
    description: str

class VideoUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None

class VideoOut(BaseModel):
    id: str
    title: str
    description: str
    preview_img: str
    video: str
    status: VideoStatus
    genre_id: Optional[uuid.UUID] = None   # 🔹 добавил
    created_at: datetime
    updated_at: datetime
    deleted_at: Optional[datetime] = None

    class Config:
        from_attributes = True



# ───────────── Books ─────────────
class BookCreate(BaseModel):
    title: str = Field(min_length=1)
    author: str = Field(min_length=1)
    description: str
    genre: Optional[str] = None
    published_year: Optional[int] = Field(default=None, ge=0, le=2100)

class BookUpdate(BaseModel):
    title: Optional[str] = None
    author: Optional[str] = None
    description: Optional[str] = None
    genre: Optional[str] = None
    published_year: Optional[int] = Field(default=None, ge=0, le=2100)
    # file_url / cover_url меняются отдельными UploadFile-эндпоинтами

class BookOut(BaseModel):
    id: uuid.UUID
    title: str
    author: str
    description: str
    genre: Optional[str]
    file_url: str
    cover_url: Optional[str]
    published_year: Optional[int]
    created_by: uuid.UUID
    created_at: datetime
    updated_at: datetime
    deleted_at: Optional[datetime] = None

    class Config:
        from_attributes = True


# ВАЖНО: починка форвард-рефов
PlaylistPublic.model_rebuild()

from __future__ import annotations

import os
import uuid
from datetime import datetime
from typing import Optional
from fastapi import HTTPException, UploadFile
from sqlmodel import Session

from app.core.config import settings
from app.core.s3 import MinioService
from app.models import Book
from app.schemas import BookCreate, BookUpdate
from app.modules.books.book_repository import BookRepository

# Разрешённые типы
ALLOWED_BOOK_MIMES = {
    "application/pdf",
    "application/epub+zip",
}
ALLOWED_COVER_PREFIX = "image/"

def _bucket() -> str:
    return getattr(settings, "AWS_S3_BUCKET_NAME", None) or os.getenv("S3_BUCKET") or "bus_storage"

def _ext_for_book(file: UploadFile) -> str:
    ct = (file.content_type or "").lower()
    if ct == "application/pdf":
        return ".pdf"
    if ct == "application/epub+zip":
        return ".epub"
    # fallback по имени файла
    ext = os.path.splitext(file.filename or "")[1].lower()
    if ext in {".pdf", ".epub"}:
        return ext
    # последний шанс — по умолчанию pdf
    return ".pdf"

def _ext_for_cover(file: UploadFile) -> str:
    ext = os.path.splitext(file.filename or "")[1].lower()
    return ext or ".jpg"


class BookService:
    def __init__(self, session: Session):
        self.session = session
        self.repo = BookRepository(session)
        self.minio = MinioService()
        self.bucket = _bucket()

    def _ensure(self, book_id: uuid.UUID) -> Book:
        book = self.repo.get(book_id)
        if not book or book.deleted_at:
            raise HTTPException(404, "Book not found")
        return book

    def presigned_links(self, book_id: uuid.UUID) -> dict:
        book = self._ensure(book_id)
        links = {}
        if book.file_url:
            key = book.file_url.replace(f"{settings.AWS_S3_PUBLIC_URL}/{self.bucket}/", "")
            links["file_url"] = self.minio.presign_get(key, bucket=self.bucket, expires_seconds=3600)
        if book.cover_url:
            key = book.cover_url.replace(f"{settings.AWS_S3_PUBLIC_URL}/{self.bucket}/", "")
            links["cover_url"] = self.minio.presign_get(key, bucket=self.bucket, expires_seconds=3600)
        return links

    # CREATE
    def create(
        self,
        *,
        created_by: uuid.UUID,
        body: BookCreate,
        file: UploadFile,
        cover: Optional[UploadFile],
    ) -> Book:
        ct = (file.content_type or "").lower()
        if ct not in ALLOWED_BOOK_MIMES and _ext_for_book(file) not in {".pdf", ".epub"}:
            raise HTTPException(400, "file must be PDF or EPUB")

        if cover and not (cover.content_type or "").lower().startswith(ALLOWED_COVER_PREFIX):
            raise HTTPException(400, "cover must be an image/*")

        new_id = uuid.uuid4()

        # book file
        file_ext = _ext_for_book(file)
        file_obj = f"books/{new_id}/file{file_ext}"
        file_url = self.minio.upload_uploadfile(file_obj, file, self.bucket)

        # cover (optional)
        cover_url = None
        if cover:
            cover_ext = _ext_for_cover(cover)
            cover_obj = f"books/{new_id}/cover{cover_ext}"
            cover_url = self.minio.upload_uploadfile(cover_obj, cover, self.bucket)

        book = Book(
            id=new_id,
            title=body.title,
            author=body.author,
            description=body.description,
            genre=body.genre,
            published_year=body.published_year,
            file_url=file_url,
            cover_url=cover_url,
            created_by=created_by,
            # created_at/updated_at у тебя уже дефолтятся в модели, можно не трогать
        )
        return self.repo.create(book)

    # READ
    def list(
        self, *,
        q: Optional[str],
        genre: Optional[str],
        author: Optional[str],
        year: Optional[int],
        limit: int,
        offset: int,
    ):
        return self.repo.list(q=q, genre=genre, author=author, year=year, limit=limit, offset=offset)

    def get(self, book_id: uuid.UUID) -> Book:
        return self._ensure(book_id)

    # UPDATE (только мета JSON)
    def update_meta(self, book_id: uuid.UUID, patch: BookUpdate) -> Book:
        book = self._ensure(book_id)
        for k, v in patch.model_dump(exclude_unset=True).items():
            setattr(book, k, v)
        return self.repo.save(book)

    # SOFT DELETE
    def soft_delete(self, book_id: uuid.UUID) -> dict:
        book = self._ensure(book_id)
        book.deleted_at = datetime.utcnow()
        self.repo.save(book)
        return {"deleted": str(book_id)}

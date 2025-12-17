from __future__ import annotations

import uuid
from typing import Annotated, Optional, List

from fastapi import APIRouter, Depends, UploadFile, File, Form, Query
from sqlmodel import Session

from app.core.db import get_session
from app.schemas import BookCreate, BookUpdate, BookOut
from app.modules.books.book_service import BookService
from app.modules.auth.auth_router import any_user_guard, admin_guard

router = APIRouter(prefix="/books", tags=["Books"])

# ---------- READ (публичный доступ на чтение по ТЗ) ----------
@router.get("", response_model=List[BookOut])
def list_books(
    q: Optional[str] = Query(None, description="query in title/author/description"),
    genre: Optional[str] = Query(None),
    author: Optional[str] = Query(None),
    year: Optional[int] = Query(None),
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    session: Session = Depends(get_session),
):
    service = BookService(session)
    return service.list(q=q, genre=genre, author=author, year=year, limit=limit, offset=offset)


@router.get("/{book_id}", response_model=BookOut)
def get_book(
    book_id: uuid.UUID,
    session: Session = Depends(get_session),
):
    service = BookService(session)
    return service.get(book_id)


@router.get("/{book_id}/links", response_model=dict)
def get_book_links(
    book_id: uuid.UUID,
    session: Session = Depends(get_session),
):
    service = BookService(session)
    return service.presigned_links(book_id)

# ---------- WRITE (только админ) ----------
@router.post("", response_model=BookOut, dependencies=[Depends(admin_guard)])
def create_book(
    title: str = Form(...),
    author: str = Form(...),
    description: str = Form(...),
    genre: Optional[str] = Form(None),              # ✅ дефолт через =
    published_year: Optional[int] = Form(None),     # ✅
    file: UploadFile = File(..., description="PDF/EPUB file"),
    cover: UploadFile = File(..., description="image/* cover"),
    session: Session = Depends(get_session),
    user=Depends(any_user_guard),
):
    body = BookCreate(
        title=title,
        author=author,
        description=description,
        genre=genre,
        published_year=published_year,
    )
    return BookService(session).create(
        created_by=uuid.UUID(user["id"]),
        body=body,
        file=file,
        cover=cover,
    )


@router.patch("/{book_id}", response_model=BookOut, dependencies=[Depends(admin_guard)])
def update_book_meta(
    book_id: uuid.UUID,
    patch: BookUpdate,
    session: Session = Depends(get_session),
):
    service = BookService(session)
    return service.update_meta(book_id, patch)



@router.delete("/{book_id}", response_model=dict, dependencies=[Depends(admin_guard)])
def delete_book(
    book_id: uuid.UUID,
    session: Session = Depends(get_session),
):
    service = BookService(session)
    return service.soft_delete(book_id)

from __future__ import annotations

import uuid
from typing import Optional, List
from datetime import datetime
from sqlmodel import Session, select

from app.models import Book


class BookRepository:
    def __init__(self, session: Session):
        self.session = session

    # CREATE
    def create(self, book: Book) -> Book:
        self.session.add(book)
        self.session.commit()
        self.session.refresh(book)
        return book

    # READ one
    def get(self, book_id: uuid.UUID) -> Optional[Book]:
        return self.session.get(Book, book_id)

    # READ many
    def list(
        self,
        *,
        q: Optional[str],
        genre: Optional[str],
        author: Optional[str],
        year: Optional[int],
        limit: int,
        offset: int,
        include_deleted: bool = False,
    ) -> List[Book]:
        stmt = select(Book)
        if not include_deleted:
            stmt = stmt.where(Book.deleted_at.is_(None))

        if q:
            like = f"%{q}%"
            stmt = stmt.where(
                (Book.title.ilike(like)) |
                (Book.author.ilike(like)) |
                (Book.description.ilike(like))
            )
        if genre:
            stmt = stmt.where(Book.genre == genre)
        if author:
            stmt = stmt.where(Book.author == author)
        if year is not None:
            stmt = stmt.where(Book.published_year == year)

        stmt = stmt.order_by(Book.created_at.desc()).limit(limit).offset(offset)
        return self.session.exec(stmt).all()

    # UPDATE (generic save)
    def save(self, book: Book) -> Book:
        book.updated_at = datetime.utcnow()
        self.session.add(book)
        self.session.commit()
        self.session.refresh(book)
        return book

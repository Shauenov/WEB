from __future__ import annotations

from typing import Iterable, Optional
from sqlmodel import Session, select

from app.models import Video, VideoStatus
from enum import Enum

class VideoRepository:
    def __init__(self, session: Session):
        self.session = session

    # CRUD
    def create(self, v: Video) -> Video:
        self.session.add(v)
        self.session.commit()
        self.session.refresh(v)
        return v

    def get(self, vid: str) -> Optional[Video]:
        return self.session.get(Video, vid)

    def list(
        self,
        status: Optional[VideoStatus],
        q: Optional[str],
        limit: int,
        offset: int,
    ) -> Iterable[Video]:
        stmt = select(Video).where(Video.deleted_at.is_(None))
        if status:
            stmt = stmt.where(Video.status == status)
        if q:
            like = f"%{q}%"
            stmt = stmt.where((Video.title.like(like)) | (Video.description.like(like)))
        stmt = stmt.order_by(Video.created_at.desc()).limit(limit).offset(offset)
        return self.session.exec(stmt).all()

    def save(self, v: Video) -> Video:
        self.session.add(v)
        self.session.commit()
        self.session.refresh(v)
        return v

from datetime import UTC, datetime
import uuid
from app.models import Music
from app.core.db import engine
from sqlmodel import Session, select
from app.schemas import CreateMusic, MusicPublic, UpdateMusic

class MusicRepository():
  def create(self, data: CreateMusic) -> MusicPublic:
    with Session(engine) as session:
        music = Music(**data.model_dump())
        session.add(music)
        session.commit()
        session.refresh(music)
        return MusicPublic.model_validate(music)
  
  def findById(self, id: str) -> MusicPublic | None:
    with Session(engine) as session:
        stmt = select(Music).where(Music.id == id).where(Music.deleted_at == None)
        result = session.exec(stmt).first()
        if not result:
           return None 
        return MusicPublic.model_validate(result)
  
  def findAll(self, skip: int | None = None, limit: int | None = None, q: str | None = None, playlist_id: uuid.UUID | None = None) -> list[MusicPublic]:
    with Session(engine) as session:
        stmt = select(Music).where(Music.deleted_at == None)
        if playlist_id:
            stmt = stmt.where(Music.playlist_id == playlist_id)
            
        if q:
            stmt = stmt.where(
                (Music.title.ilike(f"%{q}%")) | (Music.description.ilike(f"%{q}%"))
            )

        if skip:
            stmt = stmt.offset(skip)
        if limit:
            stmt = stmt.limit(limit)
        results = session.exec(stmt).all()
        return [MusicPublic.model_validate(result) for result in results]
    
  def updateById(self, id: str, data: UpdateMusic) -> MusicPublic | None:
    with Session(engine) as session:
        stmt = select(Music).where(Music.id == id)
        result = session.exec(stmt).first()
        if not result:
            return None
        
        update_data = data.model_dump(exclude_unset=True)
        for key, value in update_data.items():
            setattr(result, key, value)

        session.add(result)
        session.commit()
        session.refresh(result)
        return MusicPublic.model_validate(result)
    
  def deleteById(self, id: str) -> MusicPublic | None:
    with Session(engine) as session:
        stmt = select(Music).where(Music.id == id)
        result = session.exec(stmt).first()
        if not result:
            return None
        result.deleted_at = datetime.now(UTC)
        session.add(result)
        session.commit()
        session.refresh(result)
        return MusicPublic.model_validate(result)

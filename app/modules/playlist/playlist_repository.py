from app.models import Playlist
from app.core.db import engine
from sqlmodel import Session, select
from app.schemas import CreatePlaylist, PlaylistPublic, UpdatePlaylist

class PlaylistRepository():
  def create(self, data: CreatePlaylist) -> PlaylistPublic:
    with Session(engine) as session:
        playlist = Playlist(
            title=data.title,
            description=data.description,
            preview_img=data.preview_img
        )
        session.add(playlist)
        session.commit()
        session.refresh(playlist)
        return PlaylistPublic.model_validate(playlist)
  
  def findById(self, id: str) -> PlaylistPublic | None:
    with Session(engine) as session:
        stmt = select(Playlist).where(Playlist.id == id).where(Playlist.deleted_at == None)
        result = session.exec(stmt).first()
        if not result:
           return None 
        return PlaylistPublic.model_validate(result)
  
  def findAll(self, skip: int | None = None, limit: int | None = None, q: str | None = None) -> list[PlaylistPublic]:
    with Session(engine) as session:
        stmt = select(Playlist).where(Playlist.deleted_at == None)
        if q:
            stmt = stmt.where(
                (Playlist.title.ilike(f"%{q}%")) | (Playlist.description.ilike(f"%{q}%"))
            )
        if skip:
            stmt = stmt.offset(skip)
        if limit:
            stmt = stmt.limit(limit)
        results = session.exec(stmt).all()
        return [PlaylistPublic.model_validate(result) for result in results]
    
  def updateById(self, id: str, data: UpdatePlaylist) -> PlaylistPublic | None:
    with Session(engine) as session:
        stmt = select(Playlist).where(Playlist.id == id)
        result = session.exec(stmt).first()
        if not result:
            return None
        
        update_data = data.model_dump(exclude_unset=True)
        for key, value in update_data.items():
            setattr(result, key, value)

        session.add(result)
        session.commit()
        session.refresh(result)
        return PlaylistPublic.model_validate(result)
    
  def deleteById(self, id: str) -> PlaylistPublic | None:
    with Session(engine) as session:
        stmt = select(Playlist).where(Playlist.id == id)
        result = session.exec(stmt).first()
        if not result:
            return None
        session.delete(result)
        session.commit()
        return PlaylistPublic.model_validate(result)

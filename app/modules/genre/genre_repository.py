from datetime import datetime, UTC
from sqlmodel import Session, select
from app.models import Genre
from app.core.db import engine
from app.schemas import GenreCreate, GenreUpdate, GenrePublic


class GenreRepository():
    def __init__(self):
        return
    
    def create(self, data: GenreCreate) -> GenrePublic:
        with Session(engine) as session:
            genre = Genre(
                name=data.name,
                description=data.description,
                type=data.type   # 🔹 обязательно передавать
            )
            session.add(genre)
            session.commit()
            session.refresh(genre)
            return GenrePublic.model_validate(genre)


    def findById(self, id: str) -> GenrePublic | None:
        with Session(engine) as session:
            stmt = select(Genre).where(Genre.id == id).where(Genre.deleted_at == None)
            result = session.exec(stmt).first()
            if not result:
                return None
            return GenrePublic.model_validate(result)

    def findAll(
        self,
        skip: int | None = None,
        limit: int | None = None,
        q: str | None = None,
        type: str | None = None,
        sort_by: str = "created_at",
        order: str = "asc",
    ) -> list[GenrePublic]:
      with Session(engine) as session:
        stmt = select(Genre).where(Genre.deleted_at == None)

        if q:
            stmt = stmt.where(
                (Genre.name.ilike(f"%{q}%")) | (Genre.description.ilike(f"%{q}%"))
            )

        if type:
            stmt = stmt.where(Genre.type == type)

        allowed_sort_fields = {"name", "created_at", "updated_at", "type"}
        if sort_by not in allowed_sort_fields:
            sort_by = "created_at"

        sort_column = getattr(Genre, sort_by)
        if order == "desc":
            stmt = stmt.order_by(sort_column.desc())
        else:
            stmt = stmt.order_by(sort_column.asc())

        if skip:
            stmt = stmt.offset(skip)
        if limit:
            stmt = stmt.limit(limit)

        results = session.exec(stmt).all()
        return [GenrePublic.model_validate(result) for result in results]

    def updateById(self, id: str, data: GenreUpdate) -> GenrePublic | None:
        with Session(engine) as session:
            stmt = select(Genre).where(Genre.id == id).where(Genre.deleted_at == None)
            result = session.exec(stmt).first()
            if not result:
                return None

            update_data = data.model_dump(exclude_unset=True)
            for key, value in update_data.items():
                setattr(result, key, value)

            session.add(result)
            session.commit()
            session.refresh(result)
            return GenrePublic.model_validate(result)

    def deleteById(self, id: str) -> GenrePublic | None:
        with Session(engine) as session:
            stmt = select(Genre).where(Genre.id == id).where(Genre.deleted_at == None)
            result = session.exec(stmt).first()
            if not result:
                return None

            result.deleted_at = datetime.now(UTC)
            session.add(result)
            session.commit()
            session.refresh(result)
            return GenrePublic.model_validate(result)

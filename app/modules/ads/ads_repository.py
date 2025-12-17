from datetime import datetime, UTC
from app.models import Ad
from app.core.db import engine
from sqlmodel import Session, desc, select
from app.schemas import AdPublic, UpdateAd

class AdRepository():
    def create(self, data: Ad) -> AdPublic:
        with Session(engine) as session:
            session.add(data)
            session.commit()
            session.refresh(data)
            return AdPublic.model_validate(data)

    def findById(self, id: str) -> AdPublic | None:
        with Session(engine) as session:
            stmt = select(Ad).where(Ad.id == id, Ad.deleted_at == None)
            result = session.exec(stmt).first()
            if not result:
                return None
            return AdPublic.model_validate(result)

    def findAll(
        self,
        skip: int | None = None,
        limit: int | None = None,
        order_by: str = "date",
        q: str | None = None
    ) -> list[AdPublic]:
        with Session(engine) as session:
            stmt = select(Ad).where(Ad.deleted_at == None)

            if q:
                stmt = stmt.where(
                    (Ad.title.ilike(f"%{q}%"))
                )

            if order_by == "date":
                stmt = stmt.order_by(desc(Ad.created_at))
            elif order_by == "title":
                stmt = stmt.order_by(Ad.title)

            if skip:
                stmt = stmt.offset(skip)
            if limit:
                stmt = stmt.limit(limit)

            results = session.exec(stmt).all()
            return [AdPublic.model_validate(result) for result in results]

    def updateById(self, id: str, data: UpdateAd) -> AdPublic | None:
        with Session(engine) as session:
            stmt = select(Ad).where(Ad.id == id, Ad.deleted_at == None)
            result = session.exec(stmt).first()
            if not result:
                return None

            update_data = data.model_dump(exclude_unset=True)
            for key, value in update_data.items():
                setattr(result, key, value)

            session.add(result)
            session.commit()
            session.refresh(result)
            return AdPublic.model_validate(result)

    def deleteById(self, id: str) -> AdPublic | None:
        with Session(engine) as session:
            stmt = select(Ad).where(Ad.id == id)
            result = session.exec(stmt).first()
            if not result:
                return None
            result.deleted_at = datetime.now(UTC)
            session.add(result)
            session.commit()
            session.refresh(result)
            return AdPublic.model_validate(result)
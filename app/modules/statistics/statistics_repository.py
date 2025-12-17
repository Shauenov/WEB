from datetime import date, datetime
from typing import Optional
import uuid
from app.models import Statistics
from app.core.db import engine
from sqlmodel import Session, select
from .statistics_dto import StatisticsCreate, StatisticsPublic

class StatisticsRepository():
  def create(self, data: StatisticsCreate) -> StatisticsPublic:
    with Session(engine) as session:
        data = Statistics(**data.model_dump())
        session.add(data)
        session.commit()
        session.refresh(data)
        return StatisticsPublic.model_validate(data)
  
  def findById(self, id: str) -> StatisticsPublic | None:
    with Session(engine) as session:
        stmt = select(Statistics).where(Statistics.id == id)
        result = session.exec(stmt).first()
        if not result:
           return None 
        return StatisticsPublic.model_validate(result)
  
  def findAll(
        self,
        skip: int | None = None,
        limit: int | None = None,
        ad_id: Optional[uuid.UUID] = None,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None
    ) -> list[StatisticsPublic]:
    with Session(engine) as session:
        stmt = select(Statistics)
        if ad_id is not None:
            stmt = stmt.where(Statistics.ad_id == ad_id)
        if start_date is not None:
            start_dt = datetime.combine(start_date, datetime.min.time())
            stmt = stmt.where(Statistics.created_at >= start_dt)
        if end_date is not None:
            end_dt = datetime.combine(end_date, datetime.max.time())
            stmt = stmt.where(Statistics.created_at <= end_dt)

        stmt = stmt.order_by(Statistics.created_at, Statistics.ad_id)

        if skip:
            stmt = stmt.offset(skip)
        if limit:
            stmt = stmt.limit(limit)

        results = session.exec(stmt).all()
        return [StatisticsPublic.model_validate(result) for result in results]
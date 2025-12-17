
from datetime import datetime
from typing import List
import uuid
from pydantic import BaseModel, Field


class StatisticsBase(BaseModel):
  device_id: uuid.UUID
  ad_id: uuid.UUID
  watched_full: bool = False

class StatisticsCreate(StatisticsBase):
  pass

class StatisticsPublic(StatisticsBase):
  id: uuid.UUID
  created_at: datetime

  class Config:
      from_attributes = True

class AggregatedStatistics(BaseModel):
    unique_devices: int = Field(..., description="Количество уникальных устройств")
    watched_distribution: dict[str, float] = Field(..., description="Распределение досмотрели / не досмотрели")
    daily_views: List[dict] = Field(..., description="Динамика просмотров по дням")
    total_views: int = Field(..., description="Общее количество просмотров")
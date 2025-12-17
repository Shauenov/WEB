from collections import defaultdict
from datetime import date
from typing import Optional
import uuid
from fastapi import HTTPException
from app.core.logger import logger
from .statistics_dto import  StatisticsPublic, StatisticsCreate, AggregatedStatistics
from app.modules.statistics.statistics_repository import StatisticsRepository


class StatisticsService():
    def __init__(self):
        self.repo = StatisticsRepository()

    async def create(self, data: StatisticsCreate) -> StatisticsPublic:
        try:
            return self.repo.create(data)
        except HTTPException as e:
            raise e
        except Exception as e:
            logger.error("error %s", e)
            raise HTTPException(status_code=500, detail="Internal server error")

    def findById(self, id: str) -> StatisticsPublic | None:
        try:
            statistics = self.repo.findById(id)
            if not statistics:
                raise HTTPException(status_code=404, detail="Statistics not found")
            return statistics
        except HTTPException:
            raise
        except Exception as e:
            logger.error("error %s", e)
            raise HTTPException(status_code=500)

    def findAll(
        self,
        skip: Optional[int] = None,
        limit: Optional[int] = None,
        ad_id: Optional[uuid.UUID] = None,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None
    ) -> list[StatisticsPublic]:
        try:
            statisticss = self.repo.findAll(skip, limit, ad_id, start_date, end_date)
            return statisticss
        except Exception as e:
            logger.error("error %s", e)
            raise HTTPException(status_code=500)

    def getAggregatedStatistics(
            self,
            skip: int | None = None,
            limit: int | None = None,
            ad_id: uuid.UUID | None = None,
            start_date: date | None = None,
            end_date: date | None = None,
    ) -> AggregatedStatistics:
        try:
            records = self.repo.findAll(
                ad_id=ad_id,
                start_date=start_date,
                end_date=end_date
            )

            unique_devices = len(set(r.device_id for r in records))

            total_views = len(records)
            if total_views == 0:
                watched_distribution = {"watched": 0, "not_watched": 0}
            else:
                counts = defaultdict(int)
                for r in records:
                    key = "watched" if r.watched_full else "not_watched"
                    counts[key] += 1
                watched_distribution = {
                    k: round(v / total_views * 100, 2) for k, v in counts.items()
                }

            daily_views = defaultdict(int)
            for r in records:
                day = r.created_at.date()
                daily_views[day] += 1
            daily_views_list = [{"day": str(day), "views": count} for day, count in sorted(daily_views.items())]

            return {
                "unique_devices": unique_devices,
                "watched_distribution": dict(watched_distribution),
                "daily_views": daily_views_list,
                "total_views": total_views
            }

        except Exception as e:
            logger.error("Error aggregating statistics: %s", e)
            raise HTTPException(status_code=500, detail="Internal server error")
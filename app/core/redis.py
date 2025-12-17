# app/core/redis.py (опциональная версия)
import redis
from app.core.logger import logger
from app.core.config import settings

r = None
try:
    if settings.REDIS_HOST and settings.REDIS_PORT:
        r = redis.Redis(
            host=settings.REDIS_HOST,
            port=settings.REDIS_PORT,
            password=settings.REDIS_PASSWORD,
            socket_connect_timeout=1,
        )
        if r.ping():
            logger.info("redis: ok")
except Exception as e:
    logger.warning("redis disabled: %s", e)
    r = None

# app/core/logger.py
import logging
from multiprocessing import Queue
from app.core.config import settings

logger = logging.getLogger()
logger.setLevel(getattr(logging, getattr(settings, "LOG_LEVEL", "INFO")))

# консоль всегда
if not any(isinstance(h, logging.StreamHandler) for h in logger.handlers):
    ch = logging.StreamHandler()
    ch.setFormatter(logging.Formatter("%(asctime)s %(levelname)s %(name)s: %(message)s"))
    logger.addHandler(ch)

# loki по флагу
if getattr(settings, "ENABLE_LOKI", False) and settings.LOKI_URL:
    import logging_loki
    handler = logging_loki.LokiQueueHandler(
        queue=Queue(-1),
        url=settings.LOKI_URL,
        tags={"application": "media-admin"},
        version="1",
    )
    logger.addHandler(handler)

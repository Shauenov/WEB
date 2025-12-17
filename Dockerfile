FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

# Базовые утилиты: ffmpeg + curl (для HEALTHCHECK)
RUN apt-get update \
    && apt-get install -y --no-install-recommends \
       ffmpeg curl \
    && rm -rf /var/lib/apt/lists/*

# Зависимости
COPY ./requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r /app/requirements.txt

# Пользователь без root
RUN addgroup --system app && adduser --system --ingroup app app

# Код приложения
COPY --chown=app:app ./ /app

USER app
EXPOSE 8000

# Если у тебя есть эндпоинт /health — оставь как есть
HEALTHCHECK --interval=10s --timeout=3s --retries=10 \
  CMD curl -fsS http://localhost:8000/health || exit 1

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]

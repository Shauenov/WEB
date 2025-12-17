FROM python:3.12-slim
WORKDIR /app
EXPOSE 8000

RUN apt-get update && apt-get install --no-install-recommends git curl -y && rm -rf /var/lib/apt/lists/*

COPY ./requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir --upgrade -r /app/requirements.txt

RUN addgroup --system app && adduser --system app

RUN chown -R app:app /app
USER app

COPY --chown=app:app ./ /app

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]

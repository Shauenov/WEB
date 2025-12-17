# Bus Project (Backend + Frontend)

## Описание
Проект — медиа‑бэкенд с минимальным React UI. Поддерживает видео (HLS), музыку (HLS), книги (PDF/EPUB), плейлисты, жанры и админ‑панель управления.

## Стек
- Backend: FastAPI, SQLModel/SQLAlchemy, JWT
- Storage: MinIO (S3‑совместимое)
- Database: PostgreSQL
- Frontend: React + Vite
- Transcoding: ffmpeg/ffprobe (установлены в Docker образе backend)

## Возможности
- JWT‑аутентификация и роли (admin/user)
- CRUD для медиа
- HLS‑стриминг видео и музыки
- S3‑хранилище с presigned ссылками
- Swagger UI: `/docs`
- Логирование запросов и ошибок
- Admin dashboard для управления
- User dashboard для просмотра/прослушивания

## Base API URL
- `http://localhost:8000/api/v1`

## Тестовые учетные данные (admin)
- Телефон: `+77410000001`
- Пароль: `Admin#12345`

## Структура
- `backend/app/modules/*`: роутеры, сервисы, репозитории
- `backend/app/core/*`: конфиг, security, S3, логирование
- `backend/frontend`: React UI (admin + user)

## Установка и запуск
### Docker (рекомендуется)
Из корня репо:

```bash
cd backend
cp .env.example .env

docker compose -f compose.yml up -d --build
```

Backend API:
- http://localhost:8000
- Swagger: http://localhost:8000/docs

MinIO:
- S3 API: http://localhost:9000
- Console: http://localhost:9001

### Frontend (локально)

```bash
cd backend/frontend
cp .env.example .env
npm install
npm run dev
```

Frontend UI:
- http://localhost:5173

## Миграции
- В локальном режиме таблицы создаются автоматически (SQLModel `create_all`).
- Если используете Alembic и есть миграции, выполните:

```bash
cd backend
alembic upgrade head
```

> Убедитесь, что `DATABASE_URL` задан в `backend/.env`.

## Переменные окружения
### Backend (`backend/.env`)
Обязательно:
- `POSTGRES_HOST`, `POSTGRES_USER`, `POSTGRES_PASSWORD`, `POSTGRES_DB`, `POSTGRES_PORT`
- `DATABASE_URL` (или POSTGRES_* выше)
- `JWT_SECRET`, `JWT_REFRESH_SECRET`
- `AWS_ACCESS_KEY_ID`, `AWS_SECRET_ACCESS_KEY`
- `AWS_S3_BUCKET_NAME`
- `AWS_S3_ENDPOINT_URL` (внутренний, обычно `http://bus-minio:9000`)
- `AWS_S3_PUBLIC_URL` (публичный для браузера, например `http://localhost:9000`)

Опционально:
- `REDIS_HOST`, `REDIS_PORT`, `REDIS_PASSWORD`
- `LOG_LEVEL`, `ENABLE_METRICS`, `ENABLE_LOKI`

### Frontend (`backend/frontend/.env`)
- `VITE_API_URL=http://localhost:8000`

## Сид пользователей
Можно создать дефолтных admin и user:

```bash
docker compose -f backend/compose.yml exec bus-backend python app/seeds/seed_users.py
```

Дефолтные логины (если не переопределены ENV):
- Admin: `+77410000001` / `Admin#12345`
- User: `+77410000002` / `User#12345`

## Аутентификация
Все запросы с токеном:
`Authorization: Bearer <token>`

- `POST /api/v1/auth/sign-in`
- `POST /api/v1/auth/sign-up` (только admin)
- `POST /api/v1/auth/refresh`
- `GET /api/v1/auth/me`

## Права доступа (кратко)
User — чтение и воспроизведение. Admin — создание/изменение/удаление.

User может:
- Список/детали видео + play
- Список/детали книг + presigned ссылки
- Список/детали музыки + presigned ссылки
- Список/детали плейлистов
- Список/детали жанров
- Поиск и похожие

Admin может:
- CRUD медиа
- Управление пользователями
- Управление жанрами
- Архив/восстановление видео
- Реклама/статистика (как настроено)

## Эндпоинты
Base URL: `http://localhost:8000/api/v1`

### Auth
- `POST /auth/sign-in`
- `POST /auth/sign-up` (admin)
- `POST /auth/refresh`
- `GET /auth/me`

### Videos
- `GET /videos` (user/admin)
- `GET /videos/{vid}` (user/admin)
- `GET /videos/{vid}/play` (user/admin)
- `POST /videos` (admin)
- `PATCH /videos/{vid}` (admin)
- `DELETE /videos/{vid}` (admin)
- `POST /videos/{vid}/archive` (admin)
- `POST /videos/{vid}/restore` (admin)

`GET /videos/{vid}/play` возвращает:
- `playlist` (HLS m3u8 контент)
- `video_url` (presigned m3u8)
- `preview_url` (presigned картинка)

### Books
- `GET /books/books` (user/admin)
- `GET /books/books/{book_id}` (user/admin)
- `GET /books/books/{book_id}/links` (user/admin)
- `POST /books/books` (admin)
- `PATCH /books/books/{book_id}` (admin)
- `DELETE /books/books/{book_id}` (admin)

`GET /books/books/{book_id}/links` возвращает:
- `file_url` (presigned PDF/EPUB)
- `cover_url` (presigned картинка)

### Music
- `GET /music/musics/` (user/admin)
- `GET /music/musics/{id}` (user/admin)
- `GET /music/musics/{id}/links` (user/admin)
- `POST /music/musics/` (admin)
- `PATCH /music/musics/{id}` (admin, JSON)
- `PATCH /music/musics/{id}/media` (admin, FormData + files)
- `DELETE /music/musics/{id}` (admin)

`GET /music/musics/{id}/links` возвращает:
- `music_url` (presigned ссылка)
- `playlist` (HLS m3u8 контент, если есть)
- `preview_img` (presigned картинка)

### Playlists
- `GET /playlists/playlists/` (user/admin)
- `GET /playlists/playlists/{id}` (user/admin)
- `POST /playlists/playlists/` (admin)
- `PATCH /playlists/playlists/{id}` (admin)
- `DELETE /playlists/playlists/{id}` (admin)

### Genres
- `GET /genres/genres/` (user/admin)
- `GET /genres/genres/{id}` (user/admin)
- `POST /genres/genres/` (admin)
- `PUT /genres/genres/{id}` (admin)
- `DELETE /genres/genres/{id}` (admin)

### Users (только admin)
- `GET /users/users/`
- `GET /users/users/{id}`
- `POST /users/users/`
- `PATCH /users/users/{id}`
- `DELETE /users/users/{id}`

### Search
- `GET /search/search?q=...&type=...`
- `GET /search/search/{type}/{item_id}/similar`

### Ads
- `GET /ads/`
- `GET /ads/{id}`
- `POST /ads/` (admin)
- `DELETE /ads/{id}` (admin)

### Statistics
- `GET /statistics/` (admin)
- `GET /statistics/{id}` (admin)
- `POST /statistics/`

## Воспроизведение медиа
- Используйте `play`/`links` для получения актуальных presigned URL.
- Presigned ссылки имеют срок жизни, нужно запрашивать заново.
- В UI используется `hls.js`.

## Postman
Коллекция находится в:
- `postman/BusProject.postman_collection.json`

## Деплой
- `AWS_S3_PUBLIC_URL` должен быть публичным доменом, чтобы ссылки открывались в браузере.
- Убедитесь, что бакет доступен (public-read или presigned логика).

# app/api/main.py
from fastapi import APIRouter

# ── Core ────────────────────────────────
from app.modules.auth.auth_router import auth_router
from app.modules.user.user_router import user_router

# ── Content ─────────────────────────────
from app.modules.music.music_router import music_router
from app.modules.playlist.playlist_router import playlist_router
from app.modules.genre.genre_router import genre_router
from app.modules.videos.video_router import router as video_router
from app.modules.books.book_router import router as book_router
from app.modules.search.search_router import router as search_router

# ── Other ───────────────────────────────
from app.modules.statistics.statistics_router import statistics_router
from app.modules.ads.ads_router import ad_router
# from app.modules.stats.stats_router import stats_router  # если появится новый модуль

api_router = APIRouter()

# порядок соответствует навигации админки
api_router.include_router(auth_router, tags=["Auth"])
api_router.include_router(user_router, prefix="/users")

# контентные модули
api_router.include_router(music_router, prefix="/music", tags=["Music"])
api_router.include_router(playlist_router, prefix="/playlists", tags=["Playlists"])
api_router.include_router(genre_router, prefix="/genres", tags=["Genres"])
api_router.include_router(video_router, prefix="/videos", tags=["Videos"])
api_router.include_router(book_router, prefix="/books", tags=["Books"])
api_router.include_router(search_router, prefix="/search", tags=["Search"])

# статистика и реклама
api_router.include_router(statistics_router, prefix="/statistics", tags=["Statistics"])
api_router.include_router(ad_router, prefix="/ads", tags=["Ads"])

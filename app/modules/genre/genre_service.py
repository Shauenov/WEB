import uuid
from typing import Optional, List

from app.models import GenreType
from app.modules.genre.genre_repository import GenreRepository
from app.schemas import GenreCreate, GenreUpdate, GenrePublic


class GenreService:
    def __init__(self):
        self.repo = GenreRepository()

    def get_all(
        self,
        skip: Optional[int] = None,
        limit: Optional[int] = None,
        q: Optional[str] = None,
        type: Optional[GenreType] = None,
        sort_by: str = "created_at",
        order: str = "asc",
    ) -> List[GenrePublic]:
        return self.repo.findAll(skip=skip, limit=limit, q=q, type=type, sort_by=sort_by, order=order)
    
    def get_by_id(self, genre_id: uuid.UUID) -> Optional[GenrePublic]:
        return self.repo.findById(str(genre_id))

    def create(self, data: GenreCreate) -> GenrePublic:
        return self.repo.create(data)

    def update(self, genre_id: uuid.UUID, data: GenreUpdate) -> Optional[GenrePublic]:
        return self.repo.updateById(str(genre_id), data)

    def delete(self, genre_id: uuid.UUID) -> Optional[GenrePublic]:
        return self.repo.deleteById(str(genre_id))

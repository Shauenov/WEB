from typing import Literal, Optional
from pydantic import BaseModel


SearchType = Literal["book", "video", "music"]


class SearchResult(BaseModel):
    id: str
    type: SearchType
    title: str
    description: Optional[str] = None
    score: float


class SimilarRequest(BaseModel):
    limit: int = 10

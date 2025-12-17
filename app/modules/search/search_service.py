from __future__ import annotations

from typing import Iterable, List, Optional
from dataclasses import dataclass

from sqlmodel import Session, select
from sklearn.feature_extraction.text import TfidfVectorizer
import numpy as np

from app.models import Book, Video, Music
from app.modules.search.search_schema import SearchResult, SearchType
from app.core.logger import logger


@dataclass
class _Doc:
    id: str
    type: SearchType
    title: str
    description: str


class SearchService:
    def __init__(self, session: Session):
        self.session = session

    def _load_docs(self, type_filter: Optional[SearchType] = None) -> List[_Doc]:
        docs: list[_Doc] = []

        if type_filter in (None, "book"):
            books = self.session.exec(select(Book).where(Book.deleted_at.is_(None))).all()
            for b in books:
                docs.append(
                    _Doc(
                        id=str(b.id),
                        type="book",
                        title=b.title,
                        description=b.description or "",
                    )
                )

        if type_filter in (None, "video"):
            videos = self.session.exec(select(Video).where(Video.deleted_at.is_(None))).all()
            for v in videos:
                docs.append(
                    _Doc(
                        id=str(v.id),
                        type="video",
                        title=v.title,
                        description=v.description or "",
                    )
                )

        if type_filter in (None, "music"):
            musics = self.session.exec(select(Music).where(Music.deleted_at.is_(None))).all()
            for m in musics:
                docs.append(
                    _Doc(
                        id=str(m.id),
                        type="music",
                        title=m.title,
                        description=m.description or "",
                    )
                )

        return docs

    def _build_vectorizer(self, docs: Iterable[_Doc]) -> tuple[TfidfVectorizer, np.ndarray, list[_Doc]]:
        docs_list = list(docs)
        corpus = [f"{d.title}. {d.description}" for d in docs_list]
        if not corpus:
            return TfidfVectorizer(), np.empty((0, 0)), docs_list

        vectorizer = TfidfVectorizer(stop_words="english")
        matrix = vectorizer.fit_transform(corpus)
        return vectorizer, matrix, docs_list

    def _top_n(self, scores: np.ndarray, docs: list[_Doc], n: int) -> List[SearchResult]:
        if scores.size == 0 or not docs:
            return []
        top_idx = scores.argsort()[::-1][:n]
        results: list[SearchResult] = []
        for idx in top_idx:
            doc = docs[idx]
            results.append(
                SearchResult(
                    id=doc.id,
                    type=doc.type,
                    title=doc.title,
                    description=doc.description or None,
                    score=float(scores[idx]),
                )
            )
        return results

    def search(self, query: str, type_filter: Optional[SearchType], limit: int = 10) -> List[SearchResult]:
        docs = self._load_docs(type_filter)
        vectorizer, matrix, docs = self._build_vectorizer(docs)
        if matrix.shape[0] == 0:
            return []

        query_vec = vectorizer.transform([query])
        scores = (matrix @ query_vec.T).toarray().ravel()
        return self._top_n(scores, docs, limit)

    def similar(self, type_filter: SearchType, item_id: str, limit: int = 10) -> List[SearchResult]:
        docs = self._load_docs(type_filter)
        if not docs:
            return []

        target = next((d for d in docs if d.id == item_id), None)
        if not target:
            return []

        vectorizer, matrix, docs = self._build_vectorizer(docs)
        target_idx = next((i for i, d in enumerate(docs) if d.id == item_id), None)
        if target_idx is None or matrix.shape[0] == 0:
            return []

        target_vec = matrix[target_idx]
        scores = (matrix @ target_vec.T).toarray().ravel()
        scores[target_idx] = 0  # exclude self
        return self._top_n(scores, docs, limit)

    # --- fallbacks ---
    def _fallback_text_search(self, query: str, type_filter: Optional[SearchType], limit: int) -> List[SearchResult]:
        """Naive substring fallback when vector search is empty or errored."""
        docs = self._load_docs(type_filter)
        q_low = query.lower()
        hits = []
        for d in docs:
            text = f"{d.title} {d.description}".lower()
            if q_low in text:
                hits.append(SearchResult(id=d.id, type=d.type, title=d.title, description=d.description or None, score=1.0))
        return hits[:limit]

    def safe_search(self, query: str, type_filter: Optional[SearchType], limit: int = 10) -> List[SearchResult]:
        """Vector search with graceful fallback."""
        try:
            res = self.search(query=query, type_filter=type_filter, limit=limit)
            if res:
                return res
            return self._fallback_text_search(query, type_filter, limit)
        except Exception as e:
            logger.warning("search fallback due to error: %s", e)
            return self._fallback_text_search(query, type_filter, limit)

    def safe_similar(self, type_filter: SearchType, item_id: str, limit: int = 10) -> List[SearchResult]:
        """Similar search with graceful fallback (returns empty list on issues)."""
        try:
            res = self.similar(type_filter=type_filter, item_id=item_id, limit=limit)
            return res
        except Exception as e:
            logger.warning("similar fallback due to error: %s", e)
            return []

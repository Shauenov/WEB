from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlmodel import Session

from app.api.deps import SessionDep
from app.modules.search.search_service import SearchService
from app.modules.search.search_schema import SearchResult, SearchType
from app.modules.auth.auth_router import any_user_guard


router = APIRouter(prefix="/search", tags=["Search"])


def svc(session: Session = Depends(SessionDep)) -> SearchService:
    return SearchService(session)


@router.get("", response_model=list[SearchResult], dependencies=[Depends(any_user_guard)])
def search(
    q: str = Query(..., description="query string"),
    type: Optional[SearchType] = Query(None, description="filter by type"),
    limit: int = Query(10, ge=1, le=50),
    service: SearchService = Depends(svc),
):
    if not q.strip():
        raise HTTPException(status_code=400, detail="Query cannot be empty")
    return service.safe_search(query=q, type_filter=type, limit=limit)


@router.get("/{type}/{item_id}/similar", response_model=list[SearchResult], dependencies=[Depends(any_user_guard)])
def similar_items(
    type: SearchType,
    item_id: str,
    limit: int = Query(10, ge=1, le=50),
    service: SearchService = Depends(svc),
):
    return service.safe_similar(type_filter=type, item_id=item_id, limit=limit)

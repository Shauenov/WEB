from typing import Annotated
import uuid
from pydantic import Field
from fastapi import Form, APIRouter, UploadFile, Path, BackgroundTasks, Depends

from app.modules.ads.ads_service import AdService
from app.schemas import CreateAd, AdPublic
from app.modules.auth.auth_router import any_user_guard, admin_guard

service = AdService()

ad_router = APIRouter(
    prefix="/ads",
    tags=["Ads"],
)

@ad_router.get("/{id}", response_model=AdPublic | None)
def get_ad_by_id(
    id: Annotated[str, Path(description="The id of ad")],
    _=Depends(any_user_guard),
):
    return service.findById(id)

@ad_router.get("/", response_model=list[AdPublic])
def get_ads(
    skip: int | None = None,
    limit: int | None = None,
    order_by: str = "date",
    q: str | None = None,
    _=Depends(any_user_guard),
):
    return service.findAll(skip=skip, limit=limit, order_by=order_by, q=q)

@ad_router.post("/", response_model=AdPublic)
async def create_ad(
    title: Annotated[
        str,
        Form(...),
        Field()
    ],
    ad: UploadFile,
    background_tasks: BackgroundTasks,
    _=Depends(admin_guard),
):
    return await service.create(data=CreateAd(title=title), ad=ad, background_tasks=background_tasks)

@ad_router.delete("/{id}", response_model=AdPublic)
def delete_ad(
    id: Annotated[uuid.UUID, Path(description="The id of ad")],
    _=Depends(admin_guard),
):
    return service.deleteById(id)

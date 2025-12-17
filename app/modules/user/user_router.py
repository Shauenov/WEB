from typing import Annotated, Optional
import uuid
from pydantic import Field
from fastapi import APIRouter, Depends, Path, Body

from app.modules.user.user_service import UserService
from app.schemas import CreateUser, UpdateUser, UserPublic
from app.modules.auth.auth_router import any_user_guard


service = UserService()

user_router = APIRouter(
    prefix="/users",
    tags=["users"],
)

@user_router.get("/{id}", response_model=UserPublic | None)
def get_user_by_id(
    id: Annotated[str, Path(description="User id")],
    _=Depends(any_user_guard)
):
    return service.findById(id)

@user_router.get("/", response_model=list[UserPublic])
def get_users(
    skip: Optional[int] = None,
    limit: Optional[int] = None,
    _=Depends(any_user_guard)
):
    return service.findAll(skip=skip, limit=limit)

@user_router.post("/", response_model=UserPublic)
def create_user(
    data: CreateUser = Body(...),
    _=Depends(any_user_guard)
):
    return service.create_user(data)

@user_router.delete("/{id}", response_model=UserPublic)
def delete_user(
    id: Annotated[uuid.UUID, Path(description="User id")],
    _=Depends(any_user_guard)
):
    return service.deleteById(id)

@user_router.patch("/{id}", response_model=UserPublic)
def update_user(
    id: Annotated[uuid.UUID, Path(description="User id")],
    data: UpdateUser,
    _=Depends(any_user_guard)
):
    return service.updateById(id, data)

import uuid
from fastapi import HTTPException
from app.core.logger import logger
from app.core.security import get_hashed_password

from app.models import User
from app.schemas import CreateUser, UpdateUser, UserPublic
from app.modules.user.user_repository import UserRepository

class UserService:
    def __init__(self):
        self.repo = UserRepository()

    def create_user(self, data: CreateUser) -> UserPublic:
        try:
            # Проверка на уникальность телефона
            existing = self.repo.find_by_phone(data.phone)
            if existing:
                raise HTTPException(status_code=409, detail="Phone already registered")

            hashed = get_hashed_password(data.password)
            role = getattr(data, "role", None) or "user"

            return self.repo.create(
                User(
                    id=uuid.uuid4(),
                    fullname=data.fullname,
                    phone=data.phone,
                    password=hashed,
                    role=role,
                )
            )
        except HTTPException:
            raise
        except Exception as e:
            logger.error("create_user error: %s", e)
            raise HTTPException(status_code=500)

    def findById(self, id: str) -> UserPublic | None:
        try:
            user = self.repo.find_by_id(id)
            if not user:
                raise HTTPException(status_code=404, detail="User not found")
            return user
        except HTTPException:
            raise
        except Exception as e:
            logger.error("findById error: %s", e)
            raise HTTPException(status_code=500)

    def findAll(self, skip: int | None = None, limit: int | None = None) -> list[UserPublic]:
        try:
            return self.repo.find_all(skip, limit)
        except Exception as e:
            logger.error("findAll error: %s", e)
            raise HTTPException(status_code=500)

    def updateById(self, id: str, data: UpdateUser) -> UserPublic:
        try:
            user = self.repo.update_by_id(id, data)
            if not user:
                raise HTTPException(status_code=404, detail="User not found")
            return user
        except HTTPException:
            raise
        except Exception as e:
            logger.error("updateById error: %s", e)
            raise HTTPException(status_code=500)

    def deleteById(self, id: str) -> UserPublic | None:
        try:
            user = self.repo.delete_by_id(id)
            if not user:
                raise HTTPException(status_code=404, detail="User not found")
            return user
        except HTTPException:
            raise
        except Exception as e:
            logger.error("deleteById error: %s", e)
            raise HTTPException(status_code=500)

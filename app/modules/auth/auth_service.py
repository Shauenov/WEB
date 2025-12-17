# app/modules/auth/auth_service.py
from datetime import timedelta
from fastapi import HTTPException
from app.core.logger import logger
from app.core.security import (
    verify_password,
    get_hashed_password,
    create_access_token,
    create_refresh_token,
    decode_refresh_token,
)
from app.modules.user.user_repository import UserRepository
from app.modules.auth.auth_dto import SignInDto, SignUpDto
from app.models import User
import uuid

class AuthService:
    def __init__(self):
        self.repo = UserRepository()

    def sign_in(self, data: SignInDto):
        try:
            user = self.repo.find_by_phone(data.phone)
            if not user:
                raise HTTPException(status_code=404, detail="User not found")
            if not verify_password(data.password, user.password):
                raise HTTPException(status_code=401, detail="Invalid credentials")

            payload = {"id": str(user.id), "fullname": user.fullname, "phone": user.phone, "role": user.role}
            access = create_access_token(payload, expires_delta=timedelta(days=7))
            refresh = create_refresh_token(payload, expires_delta=timedelta(days=14))
            return {"access_token": access, "refresh_token": refresh}
        except HTTPException:
            raise
        except Exception as e:
            logger.error("sign_in error: %s", e)
            raise HTTPException(status_code=500)

    def sign_up(self, data: SignUpDto):
        try:
            if self.repo.find_by_phone(data.phone):
                raise HTTPException(status_code=409, detail="Phone already registered")
            return self.repo.create(
                User(
                    id=uuid.uuid4(),
                    fullname=data.fullname,
                    phone=data.phone,
                    password=get_hashed_password(data.password),
                    role=(data.role or "user"),
                )
            )
        except HTTPException:
            raise
        except Exception as e:
            logger.error("sign_up error: %s", e)
            raise HTTPException(status_code=500)

    def refresh(self, refresh_token: str):
        try:
            payload = decode_refresh_token(refresh_token)
            access = create_access_token(payload, expires_delta=timedelta(days=7))
            refresh = create_refresh_token(payload, expires_delta=timedelta(days=14))
            return {"access_token": access, "refresh_token": refresh}
        except HTTPException:
            raise
        except Exception as e:
            logger.error("refresh error: %s", e)
            raise HTTPException(status_code=500)

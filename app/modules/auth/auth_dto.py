# app/modules/auth/auth_dto.py
from pydantic import BaseModel, Field

PHONE_RE = r"^\+7\d{10}$"

class SignInDto(BaseModel):
    phone: str = Field(pattern=PHONE_RE, examples=["+70000000000"])
    password: str = Field(min_length=1, examples=["admin123"])

class SignUpDto(BaseModel):
    fullname: str = Field(min_length=2, examples=["Admin User"])
    phone: str = Field(pattern=PHONE_RE, examples=["+70000000000"])
    password: str = Field(min_length=8, examples=["admin123"])
    role: str | None = Field(default=None, examples=["user","admin"])

class RefreshDto(BaseModel):
    refresh_token: str = Field(min_length=10)

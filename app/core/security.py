from fastapi import HTTPException
import jwt
from app.core.config import settings
from passlib.context import CryptContext
from datetime import datetime, timedelta, timezone

pwd_context = CryptContext(schemes=["bcrypt"])

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Validate password hash safely.

    We intentionally do *not* fall back to plain-text equality to avoid
    accidentally accepting unhashed passwords if the DB contains bad data.
    """
    try:
        return pwd_context.verify(plain_password, hashed_password)
    except Exception:
        # Any verification error should be treated as a failure, not bypassed.
        return False

def get_hashed_password(plain_password: str) -> str:
    return pwd_context.hash(plain_password)

def _with_exp(data: dict, expires_delta: timedelta) -> dict:
    payload = data.copy()
    payload["exp"] = datetime.now(timezone.utc) + expires_delta
    return payload

def create_access_token(data: dict, expires_delta: timedelta) -> str:
    expires_at = datetime.now(timezone.utc) + expires_delta
    to_encode = data.copy()
    to_encode.update({"exp": expires_at})
    return jwt.encode(to_encode, settings.JWT_SECRET, algorithm="HS256")

def create_refresh_token(data: dict, expires_delta: timedelta) -> str:
    expires_at = datetime.now(timezone.utc) + expires_delta
    to_encode = data.copy()
    to_encode.update({"exp": expires_at})
    return jwt.encode(to_encode, settings.JWT_REFRESH_SECRET, algorithm="HS256")


def decode_token(token: str):
    import jwt
    try:
        payload = jwt.decode(token, settings.JWT_SECRET, algorithms=["HS256"])
        return payload
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expired")
    except jwt.InvalidTokenError as e:
        raise HTTPException(status_code=403, detail=f"Invalid token: {str(e)}")

def decode_refresh_token(token: str):
    import jwt
    try:
        payload = jwt.decode(token, settings.JWT_REFRESH_SECRET, algorithms=["HS256"])
        return payload
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Refresh token expired")
    except jwt.InvalidTokenError as e:
        raise HTTPException(status_code=403, detail=f"Invalid refresh token: {str(e)}")

from typing import Optional
from sqlmodel import Session, select
from app.core.db import engine
from app.models import User
from app.schemas import UserPublic, UpdateUser

class UserRepository:
    def create(self, data: User) -> UserPublic:
        with Session(engine) as session:
            session.add(data)
            session.commit()
            session.refresh(data)
            return UserPublic.model_validate(data)

    def find_by_id(self, id: str) -> Optional[UserPublic]:
        with Session(engine) as session:
            result = session.exec(select(User).where(User.id == id)).first()
            return UserPublic.model_validate(result) if result else None

    def find_by_phone(self, phone: str) -> Optional[User]:
        with Session(engine) as session:
            return session.exec(select(User).where(User.phone == phone)).first()

    def find_all(self, skip: int | None = None, limit: int | None = None) -> list[UserPublic]:
        with Session(engine) as session:
            stmt = select(User)
            if skip:
                stmt = stmt.offset(skip)
            if limit:
                stmt = stmt.limit(limit)
            results = session.exec(stmt).all()
            return [UserPublic.model_validate(u) for u in results]

    def update_by_id(self, id: str, data: UpdateUser) -> Optional[UserPublic]:
        with Session(engine) as session:
            user = session.exec(select(User).where(User.id == id)).first()
            if not user:
                return None
            update_data = data.model_dump(exclude_unset=True)
            for k, v in update_data.items():
                setattr(user, k, v)
            session.add(user)
            session.commit()
            session.refresh(user)
            return UserPublic.model_validate(user)

    def delete_by_id(self, id: str) -> Optional[UserPublic]:
        with Session(engine) as session:
            user = session.exec(select(User).where(User.id == id)).first()
            if not user:
                return None
            session.delete(user)
            session.commit()
            return UserPublic.model_validate(user)

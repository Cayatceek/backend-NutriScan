from sqlalchemy.orm import Session

from app.db import crud
from app.models.user import User


def get_profile(user: User) -> User:
    return user


def update_profile(db: Session, *, user: User, full_name: str | None) -> User:
    return crud.update_user_full_name(db, user=user, full_name=full_name)

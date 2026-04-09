from sqlalchemy.orm import Session

from app.db import crud
from app.models.user import User
from app.models.user_settings import UserSettings
from app.schemas.settings import UserSettingsUpdate


def get_settings_for_user(db: Session, *, user: User) -> UserSettings:
    return crud.get_or_create_user_settings(db, user.id)


def update_settings_for_user(db: Session, *, user: User, payload: UserSettingsUpdate) -> UserSettings:
    settings = crud.get_or_create_user_settings(db, user.id)
    return crud.update_user_settings(db, settings=settings, payload=payload.model_dump())

from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, get_db
from app.models.user import User
from app.schemas.settings import UserSettingsRead, UserSettingsUpdate
from app.service import settings_service

router = APIRouter(prefix="/settings", tags=["settings"])
SessionDep = Annotated[Session, Depends(get_db)]
CurrentUserDep = Annotated[User, Depends(get_current_user)]


@router.get("", response_model=UserSettingsRead)
def read_settings(db: SessionDep, current_user: CurrentUserDep) -> UserSettingsRead:
    settings = settings_service.get_settings_for_user(db, user=current_user)
    return UserSettingsRead.model_validate(settings)


@router.put("", response_model=UserSettingsRead)
def update_settings(
    payload: UserSettingsUpdate,
    db: SessionDep,
    current_user: CurrentUserDep,
) -> UserSettingsRead:
    settings = settings_service.update_settings_for_user(db, user=current_user, payload=payload)
    return UserSettingsRead.model_validate(settings)

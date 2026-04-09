from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, get_db
from app.models.user import User
from app.schemas.user import ProfileUpdateRequest, UserRead
from app.service import profile_service

router = APIRouter(prefix="/profile", tags=["profile"])
SessionDep = Annotated[Session, Depends(get_db)]
CurrentUserDep = Annotated[User, Depends(get_current_user)]


@router.get("", response_model=UserRead)
def read_profile(current_user: CurrentUserDep) -> UserRead:
    return UserRead.model_validate(profile_service.get_profile(current_user))


@router.patch("", response_model=UserRead)
def update_profile(payload: ProfileUpdateRequest, db: SessionDep, current_user: CurrentUserDep) -> UserRead:
    user = profile_service.update_profile(db, user=current_user, full_name=payload.full_name)
    return UserRead.model_validate(user)

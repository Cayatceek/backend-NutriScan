from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, get_db
from app.models.user import User
from app.schemas.auth import MessageResponse
from app.schemas.history import HistoryCreateRequest, HistoryItemRead, HistoryListResponse
from app.service import history_service

router = APIRouter(prefix="/history", tags=["history"])
SessionDep = Annotated[Session, Depends(get_db)]
CurrentUserDep = Annotated[User, Depends(get_current_user)]


@router.get("/", response_model=HistoryListResponse)
def read_history(
    db: SessionDep,
    current_user: CurrentUserDep,
    query: str | None = Query(default=None, max_length=255),
    filter: str = Query(default="all", pattern="^(all|favorites)$"),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
) -> HistoryListResponse:
    return history_service.list_history(
        db,
        user=current_user,
        query=query,
        filter_name=filter,
        page=page,
        page_size=page_size,
    )


@router.post("/", response_model=HistoryItemRead, status_code=status.HTTP_201_CREATED)
def create_history_entry(payload: HistoryCreateRequest, db: SessionDep, current_user: CurrentUserDep) -> HistoryItemRead:
    try:
        return history_service.create_history_entry(db, user=current_user, payload=payload)
    except LookupError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc


@router.delete("/{scan_id}", response_model=MessageResponse)
def delete_history_entry(scan_id: str, db: SessionDep, current_user: CurrentUserDep) -> MessageResponse:
    try:
        history_service.delete_history_entry(db, user=current_user, scan_id=scan_id)
    except LookupError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    return MessageResponse(message="History entry deleted.")


@router.delete("/", response_model=MessageResponse)
def clear_history(db: SessionDep, current_user: CurrentUserDep) -> MessageResponse:
    history_service.clear_history(db, user=current_user)
    return MessageResponse(message="History cleared.")

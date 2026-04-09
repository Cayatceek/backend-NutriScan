from __future__ import annotations

import uuid
from datetime import UTC, datetime

from sqlalchemy.orm import Session

from app.core.audit import audit_log
from app.db import crud
from app.models.user import User
from app.schemas.history import HistoryCreateRequest, HistoryItemRead, HistoryListResponse
from app.service.product_mapper import product_to_history_summary


def _to_history_item(*, scan, favorite_ids: set[int]) -> HistoryItemRead:
    return HistoryItemRead(
        id=scan.id,
        scanned_at=scan.scanned_at,
        created_at=scan.created_at,
        notes=scan.notes,
        product=product_to_history_summary(scan.product, is_favorite=scan.product_id in favorite_ids),
    )


def list_history(
    db: Session,
    *,
    user: User,
    query: str | None,
    filter_name: str,
    page: int,
    page_size: int,
) -> HistoryListResponse:
    favorites_only = filter_name == "favorites"
    offset = (page - 1) * page_size
    scans = crud.list_scan_history(
        db,
        user_id=user.id,
        query=query,
        favorites_only=favorites_only,
        limit=page_size,
        offset=offset,
    )
    total = crud.count_scan_history(db, user_id=user.id, query=query, favorites_only=favorites_only)
    favorite_ids = crud.favorite_product_ids_for_user(db, user_id=user.id, product_ids=[scan.product_id for scan in scans])
    return HistoryListResponse.build(
        items=[_to_history_item(scan=scan, favorite_ids=favorite_ids) for scan in scans],
        total=total,
        page=page,
        page_size=page_size,
    )


def create_history_entry(db: Session, *, user: User, payload: HistoryCreateRequest) -> HistoryItemRead:
    product = crud.get_product_by_id(db, payload.product_id)
    if product is None:
        raise LookupError("Product not found.")

    scan = crud.create_scan_history(
        db,
        scan_id=f"scan_{uuid.uuid4().hex}",
        user_id=user.id,
        product_id=payload.product_id,
        scanned_at=datetime.now(UTC),
        notes=payload.notes,
    )
    favorite_ids = crud.favorite_product_ids_for_user(db, user_id=user.id, product_ids=[scan.product_id])
    audit_log("history.entry.created", user_id=user.id, scan_id=scan.id, product_id=scan.product_id)
    return _to_history_item(scan=scan, favorite_ids=favorite_ids)


def delete_history_entry(db: Session, *, user: User, scan_id: str) -> None:
    scan = crud.get_scan_history(db, user_id=user.id, scan_id=scan_id)
    if scan is None:
        raise LookupError("History entry not found.")
    crud.delete_scan_history(db, scan)
    audit_log("history.entry.deleted", user_id=user.id, scan_id=scan_id)


def clear_history(db: Session, *, user: User) -> None:
    crud.delete_all_scan_history(db, user_id=user.id)
    audit_log("history.cleared", user_id=user.id)

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, get_db
from app.models.user import User
from app.schemas.auth import MessageResponse
from app.schemas.open_food_facts import OpenFoodFactsBarcodeResponse
from app.schemas.product import FavoriteProductListResponse, ProductListResponse, ProductRead
from app.service import product_service

router = APIRouter(prefix="/products", tags=["products"])
SessionDep = Annotated[Session, Depends(get_db)]
CurrentUserDep = Annotated[User, Depends(get_current_user)]


@router.get("/", response_model=ProductListResponse)
def read_products(
    db: SessionDep,
    query: str | None = Query(default=None, max_length=255),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
) -> ProductListResponse:
    return product_service.list_products(db, query=query, page=page, page_size=page_size)


@router.get("/favorites", response_model=FavoriteProductListResponse)
def read_favorite_products(
    db: SessionDep,
    current_user: CurrentUserDep,
    query: str | None = Query(default=None, max_length=255),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
) -> FavoriteProductListResponse:
    return product_service.list_favorite_products(
        db,
        user=current_user,
        query=query,
        page=page,
        page_size=page_size,
    )


@router.put("/{product_id}/favorite", response_model=MessageResponse)
def favorite_product(product_id: int, db: SessionDep, current_user: CurrentUserDep) -> MessageResponse:
    try:
        product_service.favorite_product(db, user=current_user, product_id=product_id)
    except LookupError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    return MessageResponse(message="Product added to favorites.")


@router.delete("/{product_id}/favorite", response_model=MessageResponse)
def unfavorite_product(product_id: int, db: SessionDep, current_user: CurrentUserDep) -> MessageResponse:
    try:
        product_service.unfavorite_product(db, user=current_user, product_id=product_id)
    except LookupError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    return MessageResponse(message="Product removed from favorites.")


@router.get("/barcode/{barcode}", response_model=OpenFoodFactsBarcodeResponse)
def read_product_by_barcode(barcode: str, db: SessionDep) -> OpenFoodFactsBarcodeResponse:
    return product_service.get_product_by_barcode(db, barcode)


@router.get("/{product_id}", response_model=ProductRead)
def read_product(product_id: int, db: SessionDep) -> ProductRead:
    product = product_service.get_product(db, product_id)
    if product is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Product not found.")
    return product

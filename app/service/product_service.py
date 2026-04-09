from sqlalchemy.orm import Session

from app.core.audit import audit_log
from app.db import crud
from app.models.product import Product
from app.models.user import User
from app.schemas.open_food_facts import OpenFoodFactsBarcodeResponse
from app.schemas.product import (
    FavoriteProductListResponse,
    InternalProductUpsertRequest,
    ProductListResponse,
    ProductRead,
)
from app.service import open_food_facts_service
from app.service.product_mapper import product_to_read, product_to_summary


def list_products(
    db: Session,
    *,
    query: str | None = None,
    page: int = 1,
    page_size: int = 20,
) -> ProductListResponse:
    offset = (page - 1) * page_size
    if query and query.strip():
        products = crud.search_products(db, query=query, limit=page_size, offset=offset)
    else:
        products = crud.list_products(db, limit=page_size, offset=offset)
    total = crud.count_products(db, query=query)
    return ProductListResponse.build(
        items=[product_to_read(product) for product in products],
        total=total,
        page=page,
        page_size=page_size,
    )


def get_product(db: Session, product_id: int) -> ProductRead | None:
    product = crud.get_product_by_id(db, product_id)
    return product_to_read(product) if product else None


def get_product_by_barcode(db: Session, barcode: str) -> OpenFoodFactsBarcodeResponse:
    return open_food_facts_service.get_product_by_barcode(db, barcode=barcode, prefer_local=True)


def upsert_internal_product(
    db: Session,
    *,
    payload: InternalProductUpsertRequest,
    actor: str,
) -> ProductRead:
    product = crud.upsert_product(db, payload)
    audit_log("catalog.product.upserted", actor=actor, product_id=product.id, barcode=product.barcode)
    return product_to_read(product)


def list_favorite_products(
    db: Session,
    *,
    user: User,
    query: str | None,
    page: int,
    page_size: int,
) -> FavoriteProductListResponse:
    offset = (page - 1) * page_size
    products = crud.list_favorite_products(db, user_id=user.id, query=query, limit=page_size, offset=offset)
    total = crud.count_favorite_products(db, user_id=user.id, query=query)
    return FavoriteProductListResponse.build(
        items=[product_to_summary(product, is_favorite=True) for product in products],
        total=total,
        page=page,
        page_size=page_size,
    )


def favorite_product(db: Session, *, user: User, product_id: int) -> None:
    product = crud.get_product_by_id(db, product_id)
    if product is None:
        raise LookupError("Product not found.")
    if crud.get_favorite_product(db, user_id=user.id, product_id=product_id) is None:
        crud.add_favorite_product(db, user_id=user.id, product_id=product_id)
        audit_log("favorites.product.added", user_id=user.id, product_id=product_id)


def unfavorite_product(db: Session, *, user: User, product_id: int) -> None:
    favorite = crud.get_favorite_product(db, user_id=user.id, product_id=product_id)
    if favorite is None:
        raise LookupError("Favorite not found.")
    crud.remove_favorite_product(db, favorite)
    audit_log("favorites.product.removed", user_id=user.id, product_id=product_id)

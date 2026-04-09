from __future__ import annotations

import httpx
from pydantic import ValidationError
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.db import crud
from app.schemas.open_food_facts import OpenFoodFactsBarcodeResponse, OpenFoodFactsSearchResponse
from app.service.product_mapper import product_to_barcode_response, products_to_search_response

DEFAULT_SEARCH_FIELDS = (
    "code,product_name,brands,ingredients_text,ingredients,nutriscore_grade,image_url,"
    "image_front_url,nutriments,categories,labels,additives_tags,allergens"
)


def _build_url(path: str) -> str:
    settings = get_settings()
    return f"{settings.open_food_facts_base_url.rstrip('/')}{path}"


def _fetch_json(
    path: str,
    *,
    params: dict[str, object] | None = None,
    user_agent: str | None = None,
) -> dict[str, object]:
    settings = get_settings()
    headers = {"User-Agent": user_agent or settings.open_food_facts_user_agent}
    response = httpx.get(
        _build_url(path),
        params=params,
        headers=headers,
        timeout=settings.request_timeout_seconds,
    )
    response.raise_for_status()
    return response.json()


def _local_barcode_response(barcode: str, db: Session) -> OpenFoodFactsBarcodeResponse:
    product = crud.get_product_by_barcode(db, barcode)
    if product is None:
        return OpenFoodFactsBarcodeResponse(
            code=barcode,
            product=None,
            status=0,
            status_verbose="product not found",
        )
    return product_to_barcode_response(product)


def _local_search_response(*, db: Session, query: str, page: int, page_size: int) -> OpenFoodFactsSearchResponse:
    offset = (page - 1) * page_size
    products = crud.search_products(db, query=query, limit=page_size, offset=offset)
    total = crud.count_products(db, query=query)
    return products_to_search_response(
        products=products,
        total=total,
        page=page,
        page_size=page_size,
        skip=offset,
    )


def get_product_by_barcode(
    db: Session,
    *,
    barcode: str,
    user_agent: str | None = None,
    prefer_local: bool = False,
) -> OpenFoodFactsBarcodeResponse:
    if prefer_local:
        local_response = _local_barcode_response(barcode, db)
        if local_response.status == 1:
            return local_response

    try:
        payload = _fetch_json(f"/api/v0/product/{barcode}.json", user_agent=user_agent)
        return OpenFoodFactsBarcodeResponse.model_validate(payload)
    except (httpx.HTTPError, ValidationError, ValueError):
        return _local_barcode_response(barcode, db)


def search_products(
    db: Session,
    *,
    query: str,
    page: int = 1,
    page_size: int = 20,
    fields: str = DEFAULT_SEARCH_FIELDS,
    user_agent: str | None = None,
) -> OpenFoodFactsSearchResponse:
    normalized_query = query.strip()
    if not normalized_query:
        return OpenFoodFactsSearchResponse(
            count=0,
            page=page,
            page_count=0,
            page_size=page_size,
            products=[],
            skip=(page - 1) * page_size,
        )

    try:
        payload = _fetch_json(
            "/cgi/search.pl",
            params={
                "search_terms": normalized_query,
                "page": page,
                "page_size": page_size,
                "json": 1,
                "fields": fields,
            },
            user_agent=user_agent,
        )
        return OpenFoodFactsSearchResponse.model_validate(payload)
    except (httpx.HTTPError, ValidationError, ValueError):
        return _local_search_response(db=db, query=normalized_query, page=page, page_size=page_size)

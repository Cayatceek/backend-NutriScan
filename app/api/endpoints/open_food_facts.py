from typing import Annotated

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.api.deps import get_db
from app.core.rate_limit import enforce_rate_limit, off_policy
from app.schemas.open_food_facts import OpenFoodFactsBarcodeResponse, OpenFoodFactsSearchResponse
from app.service import open_food_facts_service

router = APIRouter(tags=["open-food-facts"])
SessionDep = Annotated[Session, Depends(get_db)]
BarcodeRateLimitDep = Annotated[None, Depends(enforce_rate_limit(off_policy("off-barcode")))]
SearchRateLimitDep = Annotated[None, Depends(enforce_rate_limit(off_policy("off-search")))]


@router.get("/api/v0/product/{barcode}.json", response_model=OpenFoodFactsBarcodeResponse)
def get_product_by_barcode(barcode: str, db: SessionDep, _: BarcodeRateLimitDep) -> OpenFoodFactsBarcodeResponse:
    return open_food_facts_service.get_product_by_barcode(db, barcode=barcode, prefer_local=True)


@router.get("/cgi/search.pl", response_model=OpenFoodFactsSearchResponse)
def search_products(
    db: SessionDep,
    search_terms: str = Query(default="", max_length=255),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    json: int = Query(default=1),
    fields: str = Query(default=open_food_facts_service.DEFAULT_SEARCH_FIELDS),
    _: SearchRateLimitDep = None,
) -> OpenFoodFactsSearchResponse:
    del json
    return open_food_facts_service.search_products(
        db,
        query=search_terms,
        page=page,
        page_size=page_size,
        fields=fields,
    )

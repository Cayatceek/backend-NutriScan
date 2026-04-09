from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.deps import get_db, require_internal_api_key
from app.schemas.product import InternalProductUpsertRequest, ProductRead
from app.service import product_service

router = APIRouter(prefix="/internal", tags=["internal"])
SessionDep = Annotated[Session, Depends(get_db)]
InternalApiKeyDep = Annotated[str, Depends(require_internal_api_key)]


@router.post("/products/upsert", response_model=ProductRead)
def upsert_product(payload: InternalProductUpsertRequest, db: SessionDep, api_key: InternalApiKeyDep) -> ProductRead:
    del api_key
    return product_service.upsert_internal_product(db, payload=payload, actor="internal-api")

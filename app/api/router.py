from fastapi import APIRouter

from app.api.endpoints.auth import router as auth_router
from app.api.endpoints.health import router as health_router
from app.api.endpoints.history import router as history_router
from app.api.endpoints.internal import router as internal_router
from app.api.endpoints.open_food_facts import router as open_food_facts_router
from app.api.endpoints.products import router as products_router
from app.api.endpoints.profile import router as profile_router
from app.api.endpoints.settings import router as settings_router

compatibility_router = APIRouter()
compatibility_router.include_router(open_food_facts_router)

api_router = APIRouter()
api_router.include_router(health_router)
api_router.include_router(auth_router)
api_router.include_router(products_router)
api_router.include_router(history_router)
api_router.include_router(profile_router)
api_router.include_router(settings_router)
api_router.include_router(internal_router)

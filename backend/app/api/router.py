from fastapi import APIRouter
from .v1.auth import router as auth_router
from .v1.chat import router as chat_router
from .v1.hitl import router as hitl_router
from .v1.trips import router as trips_router

api_router = APIRouter(prefix="/api/v1")
api_router.include_router(auth_router)
api_router.include_router(trips_router)
api_router.include_router(chat_router)
api_router.include_router(hitl_router)

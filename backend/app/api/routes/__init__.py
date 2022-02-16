from fastapi import APIRouter

from app.api.routes.events import router as events_router


router = APIRouter()


router.include_router(events_router, prefix="/events", tags=["events"])

from typing import List

from fastapi import APIRouter, Body, Depends
from starlette.status import HTTP_201_CREATED

from app.models.events import EventsCreate, EventsPublic
from app.db.repositories.events import EventsRepository
from app.api.dependencies.database import get_repository


router = APIRouter()


@router.post("/", response_model=EventsPublic, name="events:create-events", status_code=HTTP_201_CREATED)
async def create_new_events(
    new_events: EventsCreate = Body(..., embed=True),
    events_repo: EventsRepository = Depends(get_repository(EventsRepository)),
) -> EventsPublic:
    created_events = await events_repo.create_events(new_events=new_events)

    return created_events

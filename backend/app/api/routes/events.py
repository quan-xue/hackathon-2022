from typing import List

from fastapi import APIRouter, Body, Depends
from starlette.status import HTTP_201_CREATED, HTTP_200_OK

from app.models.events import EventsCreate, EventsInDB, EventsPublic
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

@router.get("/", response_model=List[EventsPublic], name="events:get-events", status_code=HTTP_200_OK)
async def get_events(
    events_repo: EventsRepository = Depends(get_repository(EventsRepository)),
) -> List[EventsPublic]:
    events = await events_repo.get_events()
    return list(events)

@router.delete("/", response_model=None, name="events:delete-events", status_code=HTTP_200_OK)
async def delete_events(
    events_repo: EventsRepository = Depends(get_repository(EventsRepository)),
) -> None:
    await events_repo.delete_events()
    return None
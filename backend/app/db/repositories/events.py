from typing import List
from app.db.repositories.base import BaseRepository
from app.models.events import EventsCreate, EventsUpdate, EventsInDB


CREATE_EVENTS_QUERY = """
    INSERT INTO events (start_time, end_time, name, category, description, lat, lng, address, url, organizer, onepa_eventid)
    VALUES (:start_time, :end_time, :name, :category, :description, :lat, :lng, :address, :url, :organizer, :onepa_eventid)
    RETURNING start_time, end_time, name, category, description, lat, lng, address, url, organizer, onepa_eventid;
"""

SELECT_EVENTS_QUERY = """
    SELECT * FROM events;
"""

class EventsRepository(BaseRepository):
    """"
    All database actions associated with the Events resource
    """
    async def create_events(self, *, new_events: EventsCreate) -> EventsInDB:
        query_values = new_events.dict()
        events = await self.db.fetch_one(query=CREATE_EVENTS_QUERY, values=query_values)
        return EventsInDB(**events)

    async def get_events(self) -> List[EventsInDB]:
        events = await self.db.fetch_all(query=SELECT_EVENTS_QUERY)
        return map(lambda e: EventsInDB(**dict(e)), events)

    async def delete_events(self) -> None:
        await self.db.execute(query="DELETE from events")
        return None
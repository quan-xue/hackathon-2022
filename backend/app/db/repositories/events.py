from app.db.repositories.base import BaseRepository
from app.models.events import EventsCreate, EventsUpdate, EventsInDB


CREATE_CLEANING_QUERY = """
    INSERT INTO events (start_time, end_time, name, category, description, location, url, organizer)
    VALUES (:start_time, :end_time, :name, :category, :description, :location, :url, :organizer)
    RETURNING start_time, end_time, name, category, description, location, url, organizer;
"""


class EventsRepository(BaseRepository):
    """"
    All database actions associated with the Events resource
    """
    async def create_events(self, *, new_events: EventsCreate) -> EventsInDB:
        query_values = new_events.dict()
        events = await self.db.fetch_one(query=CREATE_EVENTS_QUERY, values=query_values)
        return EventsInDB(**events)

"""
Define 5 model types:
Base - all shared attributes of a resource
Create - attributes required to create a new resource - used at POST requests
Update - attributes that can be updated - used at PUT requests
InDB - attributes present on any resource coming out of the database
Public - attributes present on public facing resources being returned from GET, POST, and PUT requests
"""
from typing import Optional
from datetime import datetime
from enum import Enum

from geojson_pydantic.geometries import Point

from app.models.core import CoreModel, IDModelMixin


class CategoryType(str, Enum):
    official = "official"
    independent = "independent"


class EventsBase(CoreModel):
    start_time: Optional[datetime]
    end_time: Optional[datetime]
    name: Optional[str]
    category: Optional[CategoryType]
    description: Optional[str]
    url: Optional[str]
    organizer: Optional[str]
    onepa_eventid: Optional[int]


class EventsCreate(EventsBase):
    start_time: datetime
    end_time: datetime
    name: str
    category: CategoryType
    description: str
    lat: float
    lng: float


class EventsUpdate(EventsBase):
    pass


class EventsInDB(EventsBase):
    start_time: datetime
    end_time: datetime
    name: str
    category: CategoryType
    description: str
    lat: float
    lng: float
    onepa_eventid: int

class EventsPublic(EventsBase):
    lat: float
    lng: float

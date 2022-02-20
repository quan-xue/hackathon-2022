from datetime import datetime, timedelta
import logging
from dateutil import parser
from typing import Tuple
import re

from geopy.geocoders import Nominatim
from geopy.distance import distance
from pytz import timezone
import requests

# Enable logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO
)
logger = logging.getLogger(__name__)

def is_valid_postal(postal_code: str) -> bool:
    pattern = re.compile("^\d{6}$")
    match_pattern = bool(pattern.match(postal_code))
    if not match_pattern:
        return False
    else:
        return True

def search_postal(postal_code: str) -> Tuple[str, float, float]:
    """
    :param postal_code:
    :return: addr, lat, lng
    """
    query = {'searchVal': postal_code, 'returnGeom': 'Y', 'getAddrDetails':'Y'}
    api = 'https://developers.onemap.sg/commonapi/search'
    response = requests.get(api, params=query)
    results = response.json()['results']
    if not results:
        return None
    
    result = results[0]
    return {
        'address': result['ADDRESS'].title(),
        'latitude': result['LATITUDE'],
        'longitude': result['LONGITUDE']
    }

def reverse_geocode(lat, lon):
    locator = Nominatim(user_agent="kaypohBotGeocoder")
    location = locator.reverse([lat, lon])
    postcode = location.raw['address']['postcode']
    return search_postal(postcode)

def search_events(location, datetime: datetime or None):
    events = requests.get("http://server:8000/api/events").json()
    filtered_events = []

    if datetime is None:
        filtered_events = events
    else:
        query_datetime_range = [
            datetime.replace(tzinfo=None),
            datetime.replace(hour=23, minute=59, second=59, microsecond=999999).replace(tzinfo=None)
        ]
        # Find events based on the datetime of interest
        for event in events:
            start_time = parser.parse(event['start_time']).replace(tzinfo=None)
            end_time = parser.parse(event['end_time']).replace(tzinfo=None)
            if (start_time >= query_datetime_range[0] and start_time <= query_datetime_range[1]) or \
                (start_time >= query_datetime_range[0] and end_time <= query_datetime_range[1]):
                filtered_events.append(event)

    filtered_events = filter_sort_events_by_loc(location, filtered_events)

    return filtered_events

def filter_sort_events_by_loc(location, events):
    for event in events:
        search_loc = (float(location['latitude']), float(location['longitude']))
        event_loc = (event['lat'], event['lng'])
        event['dist'] = distance(event_loc, search_loc).km

    return sorted(
        filter(lambda event: event['dist'] < 5, events), 
        key=lambda event: event['dist']
    )

def format_event(db_event):
    if db_event['category'] == 'independent':
        organizer = f'@{db_event["organizer"]}'
    else:
        organizer = db_event['organizer']

    result = (
        '*1. Name of the event:*\n'
        f'{db_event["name"]}\n\n'
        '*2. Location of the event:*\n'
        f'{db_event["address"]}\n\n'
        '*3. Start time of event:*\n'
        f'{format_datetime(parser.parse(db_event["start_time"]))}\n\n'
        '*4. End time of event:*\n'
        f'{format_datetime(parser.parse(db_event["end_time"]))}\n\n'
        '*5. Description of event:*\n'
        f'{db_event["description"]}\n\n'
        '*6. Organizer:*\n'
        f'{organizer}\n\n'
    )

    if 'url' in db_event and db_event['url'] is not None:
        result += (
            '*7. URL:*\n'
            f'{db_event["url"]}\n\n'
        )
    return result

def format_datetime(val: datetime):
    return val.strftime("%d/%m/%Y, %H:%M")

def format_date(val: datetime):
    return val.strftime("%d/%m/%Y")

def parse_date(val: str):
    return parser.parse(val, dayfirst=True)
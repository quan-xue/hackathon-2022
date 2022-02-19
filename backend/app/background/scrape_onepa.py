from datetime import datetime, timedelta
from fuzzywuzzy import fuzz
import json
import asyncio
import requests
import logging
import csv

from fastapi import Body, Depends
import pendulum

from app.db.repositories.events import EventsRepository
from app.models.events import EventsCreate
from app.api.dependencies.database import get_repository

CATEGORIES = ["Active Aging",
     "Arts &amp; Culture",
     "Celebration &amp; Festivity",
     "Charity &amp; Volunteerism",
     "Chinese New Year",
     "Christmas",
     "Competitions",
     "Deepavali",
     "Exhibition &amp; Fair",
     "Hari Raya Haji",
     "Health &amp; Fitness",
     "Kopi Talks &amp; Dialogues",
     "Local Outings and Tours",
     "National Day",
     "Neighbourhood Events",
     "Oversea Outings and Tours",
     "Parenting &amp; Education"]

SG_TIMEZONE = pendulum.timezone("Asia/Singapore")

path_to_csv = "data/rc_name_coords.csv"
cc_coord_mapping = {}
with open(path_to_csv, 'r') as csvfile:
    reader = csv.reader(csvfile, delimiter=',', quotechar='|', quoting=csv.QUOTE_MINIMAL)
    for entry in reader:
        name, lat, lng = entry
        cc_coord_mapping[name] = (lat, lng)

from pprint import pprint
pprint(cc_coord_mapping)

def scrape_onepa_events():
    events = []
    path_to_events = "data/onepa-events.json"
    events = json.load(open(path_to_events))

    # Let's not spam onepa
    # for category in CATEGORIES:
    #     page = 1
    #     res_per_page = 10
    #     response = requests.get(f"https://www.onepa.gov.sg/pacesapi/eventsearch/searchjson?events=&aoi={category}&outlet=&timePeriod=&sort=rel&page={page}")
    #     res = response.json()
    #     events.extend(res["data"]["results"])
    #     total_results = res["data"]["totalResults"]
    #     max_pages = round(total_results / res_per_page)
    #     logging.info(f"Getting events for category {category}. {total_results} results in {max_pages} pages")
    #     page += 1
    #     while page < max_pages:
    #         response = requests.get(f"https://www.onepa.gov.sg/pacesapi/eventsearch/searchjson?events=&aoi=category&outlet=&timePeriod=&sort=rel&page={page}")
    #         res = response.json()
    #         logging.info(f"Getting events for category {category}, page {page}. {response.status_code}")
    #         events.extend(res["data"]["results"])
    #         page += 1

    return events


def parse_event_times(start_date, session_time):
    session_time_format = "%I:%M %p"
    start_date_format = "%d %b %Y"
    dates = [datetime.strptime(timestr, start_date_format).replace(tzinfo=SG_TIMEZONE)
             for timestr in start_date.split(" - ")]
    start_hour, end_hour = [timedelta(hours = datetime.strptime(timestr, session_time_format).hour)
                            for timestr in session_time.split(" - ")]
    is_multiday_event = len(dates) == 2

    if is_multiday_event:
        start_time = dates[0] + start_hour
        end_time = dates[1] + end_hour
    else:
        start_time = dates[0] + start_hour
        end_time = dates[0] + end_hour

    return start_time, end_time


def map_coords(event_outlet):
    matches = []
    for cc_or_rc_name in cc_coord_mapping:
        ratio = fuzz.ratio(event_outlet.lower(), cc_or_rc_name.lower())
        partial_ratio = fuzz.partial_ratio(event_outlet.lower(), cc_or_rc_name.lower())
        matches.append((ratio, partial_ratio, cc_or_rc_name))

    ratio, partial_ratio, top_match = sorted(matches, reverse=True)[0]
    logging.info(f"Top match for {event_outlet} is {top_match} with {ratio}, {partial_ratio} confidence level")

    # Arbitrary numbers
    if ratio > 90 and partial_ratio > 90:
        return top_match

    logging.info(f"Confidence level for {event_outlet} to match to a CC location too low. Skipping this event.")
    return None


def update_onepa_events(
    events_repo: EventsRepository = Depends(get_repository(EventsRepository))
):
    events = scrape_onepa_events()
    futures = []

    for event in events:
        top_match = map_coords(event["outlet"])
        if top_match is None:
            continue

        lat, lng = cc_coord_mapping[top_match]
        start_time, end_time = parse_event_times(event["startDate"], event["sessionTime"])
        new_event = {
            "new_events": {
                "start_time": start_time.timestamp(),
                "end_time": end_time.timestamp(),
                "name": event["share"]["title"],
                "category": "official",
                "description": event["share"]["description"],
                "lat": lat,
                "lng": lng,
                "url": event["share"]["url"],
                "organizer": event["organisingCommitteeName"],
                "onepa_eventid": event["eventId"],
            }
        }
        # TODO: update
        resp = requests.post("http://localhost:8000/api/events/", json=new_event)

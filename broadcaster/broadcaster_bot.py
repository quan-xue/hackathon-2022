#!/usr/bin/env python
# pylint: disable=C0116,W0613

"""
Bot for directing new joiners to their group
"""

import logging
import os
import requests
import sqlite3
import sys
from dateutil import parser
from datetime import datetime, timedelta
from geopy import distance

from telegram import Update, ParseMode
from telegram.ext import (
    CallbackContext
)
from telegram.ext import Updater, CommandHandler
import pandas as pd

sys.path.append('../')
from listener.psa_listener import ALL_KAMPONGS
from moderator import moderator


BOT_TOKEN = os.getenv('PSA_BROADCASTER_BOT_TOKEN')
BROADCAST_POLL_INTERVAL = 10  # in seconds
EVENT_AGGREGATION_INTERVAL = int(os.getenv('EVENT_AGGREGATION_INTERVAL'))

# Enable logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO
)

logger = logging.getLogger(__name__)

CC_LOCATION = pd.read_csv('data/cc_name_coords_link.csv')
CHAT_ID_LOCATION_MAPPING = {}
for _, row in CC_LOCATION.iterrows():
    if not pd.isna(row['chat_id']):
        chat_id = row['chat_id']
        lat, lng = row['lat'], row['long']
        CHAT_ID_LOCATION_MAPPING[chat_id] = (lat, lng)


def fetch_and_send(context: CallbackContext):
    kampong = context.job.context['kampong']
    chat_id = context.job.context['chat_id']
    con = sqlite3.connect(os.getenv('PUBLIC_ADVISORY_DB_PATH'))
    cur = con.cursor()
    query = f"select message from {os.getenv('PUBLIC_ADVISORY_TABLE_MESSAGE')} where kampong='{kampong}' or kampong='{ALL_KAMPONGS}';"
    messages = [r[0] for r in cur.execute(query).fetchall()]

    # remove messages
    delete_query = f"DELETE FROM {os.getenv('PUBLIC_ADVISORY_TABLE_MESSAGE')} WHERE kampong='{kampong}' or kampong='{ALL_KAMPONGS}';"
    cur.execute(delete_query)
    con.commit()
    con.close()

    for message in messages:
        context.bot.send_message(chat_id=chat_id, text=message, parse_mode=ParseMode.MARKDOWN)


def filter_events(events, chat_id):
    # Sanity checks
    logger.info(CHAT_ID_LOCATION_MAPPING)
    filter_count = 0

    dist_mapping = {}

    for event in events:
        # TODO: better time check
        now = datetime.now()
        # TODO: return timezone info in events API response
        event_time = parser.parse(event['start_time']).replace(tzinfo=None) + timedelta(hours=8)
        is_within_one_week_ahead = (event_time - now) > timedelta(days=7)
        if not is_within_one_week_ahead:
            filter_count += 1
            continue

        kampong_latlng = CHAT_ID_LOCATION_MAPPING[chat_id]
        lat, lng = event["lat"], event["lng"]
        dist = distance.distance(kampong_latlng, (lat, lng)).kilometers
        dist_mapping[dist] = event

    # TODO: get top 3 by nearest location
    keys = sorted(dist_mapping.keys())[:3]
    logger.info(f"Nearest locations: {keys}. Filtered out {filter_count} entries outside of 1 week window.")
    return [dist_mapping[k] for k in keys]


def format_time(time):
    # TODO: return timezone info in events API response
    return (parser.parse(time) + timedelta(hours=8)).strftime("%d %b %y, %I:%M %p")


def format_events(events):
    events_str = ["What's cooking in the week ahead? 🕺"]
    for event in events:
        name = event["name"]
        organizer = event["organizer"]
        address = event["address"]
        start, end = format_time(event['start_time']), format_time(event['start_time'])
        description = event["description"]
        eventstr = (
            f'🎉 {name} organized by 🙆‍♂ {organizer}\n'
            f'📍 {address}\n'
            f'🕔 {start} to {end}\n'
            f'✉️ {description}\n'
        )

        if "url" in event and event["url"] is not None:
            url = event["url"]
            eventstr += f"{url}\n"

        events_str.append(eventstr)

    event_str_separator = "\n\n"

    return event_str_separator.join(events_str)



def aggregate_events(context: CallbackContext):
    kampong = context.job.context['kampong']
    chat_id = context.job.context['chat_id']

    events = requests.get("http://server:8000/api/events").json()
    logger.info(f"{events[0]}")

    message = format_events(filter_events(events, chat_id))

    context.bot.send_message(chat_id=chat_id, text=message, parse_mode=ParseMode.MARKDOWN)


def broadcast_events(update: Update, context: CallbackContext):
    logger.info('Broadcast event aggregation cronjob started.')
    kampong = 'Kolam Ayer'
    chat_id = update.message.chat_id
    job_context = {
        'chat_id': chat_id,
        'kampong': kampong
    }
    logger.info(f"Event aggregation for kampong {kampong} with chat_id: {chat_id}")

    context.job_queue.run_repeating(aggregate_events, interval=EVENT_AGGREGATION_INTERVAL, context=job_context)


def broadcast_start(update: Update, context: CallbackContext):
    logger.info('Broadcast polling started.')
    kampong = 'Kolam Ayer'
    job_context = {
        'chat_id': update.message.chat_id,
        'kampong': kampong
    }
    logger.info(f"Broadcasting for Kampong: {kampong}")

    context.job_queue.run_repeating(fetch_and_send, interval=BROADCAST_POLL_INTERVAL, context=job_context)


def main() -> None:
    """Run the bot."""
    # Create the Updater and pass it your bot's token.
    updater = Updater(BOT_TOKEN)

    # Get the dispatcher to register handlers
    dispatcher = updater.dispatcher

    # add psa broadcaster
    dispatcher.add_handler(CommandHandler('broadcaststart', broadcast_start))

    # moderator bot
    dispatcher.add_handler(moderator)

    # add kang ren's event broadcaster here
    dispatcher.add_handler(CommandHandler('broadcaststart', broadcast_events))

    # Start the Bot
    updater.start_polling()

    # Run the bot until you press Ctrl-C or the process receives SIGINT,
    # SIGTERM or SIGABRT. This should be used most of the time, since
    # start_polling() is non-blocking and will stop the bot gracefully.
    updater.idle()


if __name__ == '__main__':
    main()

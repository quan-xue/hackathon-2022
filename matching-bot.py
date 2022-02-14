#!/usr/bin/env python
# pylint: disable=C0116,W0613

"""
Bot for directing new joiners to their gorup
"""

import logging
import os
import re
from typing import Tuple

import pandas as pd
import requests
from dotenv import load_dotenv
from geopy import distance
from telegram import ReplyKeyboardMarkup, ReplyKeyboardRemove, Update
from telegram.ext import (
    Updater,
    CommandHandler,
    MessageHandler,
    Filters,
    ConversationHandler,
    CallbackContext,
)

load_dotenv()

BOT_TOKEN = os.getenv('BOT_TOKEN')

# Enable logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO
)

logger = logging.getLogger(__name__)

ENTERED_NAME, POSTAL_VALIDATE, POSTAL_PASSED, MATCHED = range(4)
CONFIRMATION_POSITIVE = 'Yep correct.'
CONFIRMATION_NEGATIVE = 'Nope, let me key in again.'


def start(update: Update, context: CallbackContext) -> int:
    """Starts the conversation and asks the user for their name."""
    update.message.reply_text(
        'Har-lo! My name is KayPoh Bot. \n'
        'What\'s your name? \n'
        'Send /cancel to stop talking to me.\n\n'
        ),

    return ENTERED_NAME


def location(update: Update, context: CallbackContext) -> int:
    """Stores the selected name and asks for their location."""
    context.user_data['name'] = update.message.text
    logger.info("Preferred way of being addressed: %s", context.user_data['name'])
    update.message.reply_text(f'Hi {update.message.text}, nice to meet you! Can let me kay-poh your postal code?', reply_markup=ReplyKeyboardRemove())

    return POSTAL_VALIDATE


def check_postal_validity(update: Update, context: CallbackContext) -> int:
    pattern = re.compile("^\d{6}$")
    postal = update.message.text
    match_pattern = bool(pattern.match(postal))
    if not match_pattern:
        logger.info("Postal %s failed. Asking for input again.", postal)
        update.message.reply_text(f'You entered {postal}. Doesn\'t seem right leh... Must be 6-digit (e.g. 012345) hor. Try again?', reply_markup=ReplyKeyboardRemove())
        return POSTAL_VALIDATE
    else:
        logger.info("Postal %s passed.", postal)
        context.user_data['postal'] = postal
        addr, lat, lng = get_addr_lat_lng(context.user_data['postal'])
        context.user_data['lat_lng'] = (lat, lng)
        logger.info("Address: %s Lat: %s Lng: %s", addr, lat, lng)
        keyboard = [[CONFIRMATION_POSITIVE, CONFIRMATION_NEGATIVE]]
        update.message.reply_text(
            f'{context.user_data["name"]}, does this address look right? \n{addr}',
            reply_markup=ReplyKeyboardMarkup(keyboard, one_time_keyboard=True)
        )

        return POSTAL_PASSED


def match_group(update: Update, context: CallbackContext) -> int:
    chosen_rc, link = find_closest_rc(context.user_data['lat_lng'])
    logger.info("Chosen rc: %s Group link: %s", chosen_rc, link)
    update.message.reply_text(
        f'Yay! We found your kampong. \nTelegram group name: {chosen_rc}\nTelegram link: {link}\n'
        f'Join and have fun kay-pohing!'
    )

    return ConversationHandler.END


def get_addr_lat_lng(postal_code) -> Tuple[str, float, float]:
    """
    :param postal_code:
    :return: addr, lat, lng
    """
    query = {'searchVal': postal_code, 'returnGeom': 'Y', 'getAddrDetails':'Y'}
    api = 'https://developers.onemap.sg/commonapi/search'
    response = requests.get(api, params=query)
    res = response.json()['results'][0] # take the first result
    addr = res['ADDRESS'].title()
    lat, lng = res['LATITUDE'], res['LONGITUDE']

    return addr, float(lat), float(lng)


def find_closest_rc(lat_lng: Tuple[float, float]):
    min_dist = 9999
    chosen_rc = ''
    link = ''
    for _, row in RC_LOCATION.iterrows():
        curr_dist = distance.distance(lat_lng, (row['lat'], row['long'])).kilometers
        if curr_dist < min_dist:
            chosen_rc = row['name']
            min_dist = curr_dist
            link = row['group_link']
    return chosen_rc, link


def cancel(update: Update, context: CallbackContext) -> int:
    """Cancels and ends the conversation."""
    user = update.message.from_user
    logger.info("User %s canceled the conversation.", user.first_name)
    update.message.reply_text(
        'Bye! I hope we can talk again some day.', reply_markup=ReplyKeyboardRemove()
    )

    return ConversationHandler.END


def main() -> None:
    """Run the bot."""
    # Create the Updater and pass it your bot's token.
    updater = Updater(BOT_TOKEN)

    # Get the dispatcher to register handlers
    dispatcher = updater.dispatcher

    conv_handler = ConversationHandler(
        entry_points=[CommandHandler('start', start)],
        states={
            ENTERED_NAME: [MessageHandler(Filters.text, location)],
            POSTAL_VALIDATE: [MessageHandler(Filters.text, check_postal_validity)],
            POSTAL_PASSED: [
                MessageHandler(
                    Filters.regex(f'^{CONFIRMATION_POSITIVE}$'), match_group
                ),
                MessageHandler(Filters.regex(f'^{CONFIRMATION_NEGATIVE}$'), location),
            ]

        },
        fallbacks=[CommandHandler('cancel', cancel)],
    )

    dispatcher.add_handler(conv_handler)

    # Start the Bot
    updater.start_polling()

    # Run the bot until you press Ctrl-C or the process receives SIGINT,
    # SIGTERM or SIGABRT. This should be used most of the time, since
    # start_polling() is non-blocking and will stop the bot gracefully.
    updater.idle()


if __name__ == '__main__':
    RC_LOCATION = pd.read_csv('rc data/rc_name_coords_link.csv')
    main()

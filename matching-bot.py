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
from telegram import ReplyKeyboardRemove, Update, InlineKeyboardButton, InlineKeyboardMarkup, ParseMode
from telegram.ext import (
    Updater,
    CommandHandler,
    MessageHandler,
    Filters,
    ConversationHandler,
    CallbackContext, CallbackQueryHandler,
)

load_dotenv()

BOT_TOKEN = os.getenv('BOT_TOKEN')

# Enable logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO
)

logger = logging.getLogger(__name__)

ENTERED_NAME, CHECK_POSTAL, POSTAL_VALIDATED, MATCHED = range(4)
CONFIRMATION_POSITIVE = 'Yep correct 👍'
CONFIRMATION_NEGATIVE = 'Nope, wrong liao 👎'
GROUP_IDENTIFIER = '[Kaypoh @ Kampong]'


def start(update: Update, context: CallbackContext) -> int:
    """Starts the conversation and asks the user for their name."""
    update.message.reply_text(
        'Har-lo! My name is KayPoh Bot. \n'
        'What\'s your *name*? \n'
        'Send /cancel to end my kay-poh.\n\n',
        parse_mode=ParseMode.MARKDOWN
        ),

    return ENTERED_NAME


def location(update: Update, context: CallbackContext) -> int:
    """Stores the selected name and asks for their location."""
    context.user_data['name'] = update.message.text
    logger.info("Preferred way of being addressed: %s", context.user_data['name'])
    update.message.reply_text(f'👋 {update.message.text}, nice to meet you! '
                              f'Can let me kay-poh your *postal code* (e.g.123456)?',
                              reply_markup=ReplyKeyboardRemove(),
                              parse_mode=ParseMode.MARKDOWN)

    return CHECK_POSTAL


def retry_location(update: Update, context: CallbackContext) -> int:
    query = update.callback_query
    query.answer()  # CallbackQueries need to be answered, even if no notification to the user is needed
    query.message.reply_text(f'No problem. What\'s your *postal code* (e.g.123456)?',
                             reply_markup=ReplyKeyboardRemove(),
                             parse_mode=ParseMode.MARKDOWN)

    return CHECK_POSTAL


def check_postal_validity(update: Update, context: CallbackContext) -> int:
    pattern = re.compile("^\d{6}$")
    postal = update.message.text
    match_pattern = bool(pattern.match(postal))

    if not match_pattern:
        logger.info("Postal %s failed. Asking for input again.", postal)
        update.message.reply_text(f'Doesn\'t seem right leh... Must be *6-digit* (e.g. 123456) hor. You entered *{postal}*. Try again?',
                                  reply_markup=ReplyKeyboardRemove(),
                                  parse_mode=ParseMode.MARKDOWN)
        return CHECK_POSTAL

    logger.info("Postal basic syntax %s passed.", postal)
    context.user_data['postal'] = postal
    r = search_postal(context.user_data['postal'])
    if not r:
        update.message.reply_text(f'🤔 Cannot find this address... You entered *{postal}*. Try again?',
                                  reply_markup=ReplyKeyboardRemove(),
                                  parse_mode=ParseMode.MARKDOWN)
        return CHECK_POSTAL

    res = r[0]  # take first result
    addr = res['ADDRESS'].title()
    lat, lng = res['LATITUDE'], res['LONGITUDE']
    context.user_data['lat_lng'] = (lat, lng)
    logger.info("Address: %s Lat: %s Lng: %s", addr, lat, lng)
    keyboard = [
        [
            InlineKeyboardButton(CONFIRMATION_POSITIVE, callback_data=CONFIRMATION_POSITIVE),
            InlineKeyboardButton(CONFIRMATION_NEGATIVE, callback_data=CONFIRMATION_NEGATIVE),
        ]
    ]
    update.message.reply_text(
        f'Does this *address* look right? \n{addr}',
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode=ParseMode.MARKDOWN
    )

    return POSTAL_VALIDATED


def match_group(update: Update, context: CallbackContext) -> int:
    query = update.callback_query
    query.answer()  # CallbackQueries need to be answered, even if no notification to the user is needed
    chosen_group, link = find_closest(context.user_data['lat_lng'])
    logger.info("Chosen rc: %s Group link: %s", chosen_group, link)
    query.message.reply_text(
        f'We found your kampong 🙌 🙌  \nTelegram group name: {GROUP_IDENTIFIER} {chosen_group}\nTelegram link: {link}\n'
        f'Join in and have fun kay-pohing 😎'
    )
    query.message.reply_text(
        'When you join the group, you may notice that there are bots for publicizing community events, '
        'broadcasting public advisories and many more. '
        'Fret not, these bots won\'t be able to read your messages because nobody likes being snooped on. '
        'We get it. We want our favorite chicken rice stall to be our '
        'kampong\'s best kept secret too. 🙈\n'
        'All the bots are in _privacy mode_. '
        'Don\'t take our word for it, here is the official notice by Telegram!\n'
        'https://core.telegram.org/bots#privacy-mode',
        parse_mode=ParseMode.MARKDOWN
    )

    return ConversationHandler.END


def search_postal(postal_code) -> Tuple[str, float, float]:
    """
    :param postal_code:
    :return: addr, lat, lng
    """
    query = {'searchVal': postal_code, 'returnGeom': 'Y', 'getAddrDetails':'Y'}
    api = 'https://developers.onemap.sg/commonapi/search'
    response = requests.get(api, params=query)
    return response.json()['results']


def find_closest(lat_lng: Tuple[float, float]):
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
        'Cya!', reply_markup=ReplyKeyboardRemove()
    )

    return ConversationHandler.END


def help_command(update: Update, context: CallbackContext) -> None:
    """Displays info on how to use the bot."""
    update.message.reply_text("Type /start to find your kampong!")


def main() -> None:
    """Run the bot."""
    # Create the Updater and pass it your bot's token.
    updater = Updater(BOT_TOKEN)

    # Get the dispatcher to register handlers
    dispatcher = updater.dispatcher

    conv_handler = ConversationHandler(
        entry_points=[CommandHandler('start', start)],
        states={
            ENTERED_NAME: [MessageHandler(Filters.text & (~Filters.command), location)],
            CHECK_POSTAL: [MessageHandler(Filters.text & (~Filters.command), check_postal_validity)],
            POSTAL_VALIDATED: [
                CallbackQueryHandler(
                    match_group,
                    pattern=f'^{CONFIRMATION_POSITIVE}$',
                ),
                CallbackQueryHandler(
                    retry_location,
                    pattern=f'^{CONFIRMATION_NEGATIVE}$',
                )
            ]

        },
        fallbacks=[CommandHandler('cancel', cancel)],
    )

    dispatcher.add_handler(conv_handler)

    dispatcher.add_handler(CommandHandler('help', help_command))

    # Start the Bot
    updater.start_polling()

    # Run the bot until you press Ctrl-C or the process receives SIGINT,
    # SIGTERM or SIGABRT. This should be used most of the time, since
    # start_polling() is non-blocking and will stop the bot gracefully.
    updater.idle()


if __name__ == '__main__':
    RC_LOCATION = pd.read_csv('cc data/cc_name_coords_link.csv')  # persisted in memory
    main()

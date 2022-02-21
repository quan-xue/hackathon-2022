#!/usr/bin/env python
# pylint: disable=C0116,W0613

"""
Bot for directing new joiners to their group
"""

import logging
from typing import Tuple

import pandas as pd
from geopy import distance
from telegram import ReplyKeyboardRemove, Update, InlineKeyboardButton, InlineKeyboardMarkup, ParseMode
from telegram.ext import (
    ConversationHandler,
    CallbackContext, CommandHandler, MessageHandler, Filters, CallbackQueryHandler, )

from util import is_valid_postal, search_postal

# Enable logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO
)

logger = logging.getLogger(__name__)

ENTERED_NAME, CHECK_POSTAL, POSTAL_VALIDATED, PLEDGE_RESPONSE, MATCHED = range(5)
ADDR_CONFIRMATION_POSITIVE = 'Yep looks right 👍'
ADDR_CONFIRMATION_NEGATIVE = 'Nope wrong liao 👎'

PLEDGE_CONFIRMATION_POSITIVE = 'Okay I promise! 😇'
PLEDGE_CONFIRMATION_NEGATIVE = 'Nope'
GROUP_IDENTIFIER = '[Kaypoh @ Kampong]'
CC_LOCATION = pd.read_csv('data/cc_name_coords_link.csv')


def join(update: Update, context: CallbackContext) -> int:
    """Starts the conversation and asks the user for their name."""
    update.message.reply_text(
        'Har-lo! What\'s your *name*? \n'
        'Send /cancel to end my kay-poh.\n',
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
    query.answer("You have indicated that the postal code is wrong.")
    query.message.reply_text(f'No problem. What\'s your *postal code* (e.g.123456)?',
                             reply_markup=ReplyKeyboardRemove(),
                             parse_mode=ParseMode.MARKDOWN)

    return CHECK_POSTAL


def check_postal_validity(update: Update, context: CallbackContext) -> int:
    postal = update.message.text

    if not is_valid_postal(postal):
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

    logger.info(f"Group is at {r['address']}, {r['latitude']}, {r['longitude']}")
    context.user_data['lat_lng'] = (r['latitude'], r['longitude'])
    keyboard = [
        [
            InlineKeyboardButton(ADDR_CONFIRMATION_POSITIVE, callback_data=ADDR_CONFIRMATION_POSITIVE),
            InlineKeyboardButton(ADDR_CONFIRMATION_NEGATIVE, callback_data=ADDR_CONFIRMATION_NEGATIVE),
        ]
    ]
    update.message.reply_text(
        f'Does this *address* look right?\n{r["address"]}\n(select an option below)',
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode=ParseMode.MARKDOWN
    )

    return POSTAL_VALIDATED


def pledge(update: Update, context: CallbackContext) -> int:
    query = update.callback_query
    query.answer("You have confirmed your address.")
    keyboard = [
        [
            InlineKeyboardButton(PLEDGE_CONFIRMATION_POSITIVE, callback_data=PLEDGE_CONFIRMATION_POSITIVE),
            InlineKeyboardButton(PLEDGE_CONFIRMATION_NEGATIVE, callback_data=PLEDGE_CONFIRMATION_NEGATIVE),
        ]
    ]
    query.message.reply_text(
        f"We found your kampong, {context.user_data['name']}! 🙌 🙌 Before we can let you in, "
        f"do you promise to be *respectful* of others in your kampong? "
        "No *ageism*, *racism*, *sexism*, *xenophobia*, or any other bad vibes okay? (select an option below)",
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode=ParseMode.MARKDOWN
    )

    return PLEDGE_RESPONSE


def match_group(update: Update, context: CallbackContext) -> int:
    query = update.callback_query
    chosen_group, link = find_closest(context.user_data['lat_lng'])
    logger.info("Chosen group: %s Group link: %s", chosen_group, link)
    query.answer("Thanks for making our community a safe and pleasant space for all!")
    query.message.reply_text(
        f'Join in and have fun kay-pohing 😎\n'
        f'Telegram group name: {GROUP_IDENTIFIER} {chosen_group}\nTelegram link: {link}\n'
    )

    return ConversationHandler.END


def find_closest(lat_lng: Tuple[float, float]):
    min_dist = 9999
    chosen_rc = ''
    link = ''
    for _, row in CC_LOCATION.iterrows():
        curr_dist = distance.distance(lat_lng, (row['lat'], row['long'])).kilometers
        if curr_dist < min_dist:
            chosen_rc = row['name']
            min_dist = curr_dist
            link = row['group_link']
    return chosen_rc, link


def reject_pledge(update: Update, context: CallbackContext) -> int:
    query = update.callback_query
    logger.info("Reject pledge")
    query.answer()
    query.message.reply_text("Sorry to hear that... Hope you can join us in the future!")

    return ConversationHandler.END


def cancel(update: Update, context: CallbackContext) -> int:
    """Cancels and ends the conversation."""
    update.message.reply_text(
        'Cya! Hope you can join us next time.', reply_markup=ReplyKeyboardRemove()
    )

    return ConversationHandler.END


matching_convo = ConversationHandler(
    entry_points=[CommandHandler('join', join)],
    states={
        ENTERED_NAME: [MessageHandler(Filters.text & (~Filters.command), location)],
        CHECK_POSTAL: [MessageHandler(Filters.text & (~Filters.command), check_postal_validity)],
        POSTAL_VALIDATED: [
            CallbackQueryHandler(
                pledge,
                pattern=f'^{ADDR_CONFIRMATION_POSITIVE}$',
            ),
            CallbackQueryHandler(
                retry_location,
                pattern=f'^{ADDR_CONFIRMATION_NEGATIVE}$',
            )
        ],
        PLEDGE_RESPONSE: [
            CallbackQueryHandler(
                match_group,
                pattern=f'^{PLEDGE_CONFIRMATION_POSITIVE}$'
            ),
            CallbackQueryHandler(
                reject_pledge,
                pattern=f'^{PLEDGE_CONFIRMATION_NEGATIVE}$'
            )
        ]

    },
    fallbacks=[CommandHandler('cancel', cancel)],
)

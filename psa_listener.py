#!/usr/bin/env python
# pylint: disable=C0116,W0613

"""
Bot for directing new joiners to their group
"""

import logging
import sqlite3
from sqlite3.dbapi2 import Cursor
from typing import Tuple, List

from dotenv import load_dotenv
from telegram import ReplyKeyboardRemove, Update, InlineKeyboardButton, InlineKeyboardMarkup, ParseMode
from telegram.ext import (
    CommandHandler,
    MessageHandler,
    Filters,
    ConversationHandler,
    CallbackContext, CallbackQueryHandler
)

from psa_setup_db import DB_NAME, TABLE_AGENCY, TABLE_MESSAGE

load_dotenv()

# Enable logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO
)

logger = logging.getLogger(__name__)

SELECT_KAMPONG, ENTERED_MESSAGE, VERIFY_MESSAGE, CONFIRMED_MESSAGE = range(4)
MESSAGE_CONFIRMATION_POSITIVE = 'Good to go.'
MESSAGE_CONFIRMATION_NEGATIVE = 'Nope, let me edit my message.'
ALL_KAMPONGS = 'All of the above'


def get_agency_info(cur: Cursor, username: str) -> Tuple[str, List[str]]:
    """Query db for agency and kampong allowed for broadcasting"""
    query = f"select agency, kampong from {TABLE_AGENCY} where telegram_handle='{username}';"
    r = cur.execute(query).fetchall()
    agency = r[0][0]
    kampongs = [kampong for _, kampong in r]
    logger.info(f'Agency: {agency} from {username}. Kampongs: {kampongs}')

    return agency, kampongs


def broadcast(update: Update, context: CallbackContext) -> int:
    """Initiates the conversation and select the kampong(s) to broadcast to"""
    con = sqlite3.connect(DB_NAME)
    cur = con.cursor()
    username = update.message.from_user.username
    agency, kampongs = get_agency_info(cur, username)
    con.close()

    context.user_data['agency'] = agency
    keyboard = [
        [InlineKeyboardButton(kampong, callback_data=kampong) for kampong in kampongs] +
        [InlineKeyboardButton(ALL_KAMPONGS, callback_data=ALL_KAMPONGS)]
    ]

    update.message.reply_text(
        f'Hi {username} from {agency}. Which kampong(s) would you like to broadcast to? (select an option below)\n'
        f'Send /cancel to end the conversation.\n',
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

    return SELECT_KAMPONG


def draft_message(update: Update, context: CallbackContext) -> int:
    """Asks for the message to be broadcast"""
    print(update.to_dict())
    print(update.callback_query.data)
    query = update.callback_query
    context.user_data['broadcast_target'] = update.callback_query.data
    logger.info(f"Selected kampong to broadcast to: {context.user_data['broadcast_target']}")
    query.answer()
    query.message.reply_text(
        f"You have selected '{context.user_data['broadcast_target']}'. What would you like to tell the kampong?"
    )

    return ENTERED_MESSAGE


def edit_message(update: Update, context: CallbackContext) -> int:
    query = update.callback_query
    query.message.reply_text(
        f"No worries. What would you like to tell the kampong?"
    )

    return ENTERED_MESSAGE


def verify_message(update: Update, context: CallbackContext) -> int:
    """Shows message being sent"""
    message = f"⚠️Public announcement from *{context.user_data['agency']}*⚠\n{update.message.text}"
    context.user_data['message'] = message
    logger.info(f"Message: {context.user_data['message']}")
    keyboard = [
        [
            InlineKeyboardButton(MESSAGE_CONFIRMATION_POSITIVE, callback_data=MESSAGE_CONFIRMATION_POSITIVE),
            InlineKeyboardButton(MESSAGE_CONFIRMATION_NEGATIVE, callback_data=MESSAGE_CONFIRMATION_NEGATIVE),
        ]
    ]
    update.message.reply_text(
        f'This is how your message is going to look like\n........\n{message}\n........\n'
        f'Does it look okay? (select an option below)',
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode=ParseMode.MARKDOWN
    )

    return VERIFY_MESSAGE


def confirm_message(update: Update, context: CallbackContext) -> int:
    query = update.callback_query
    query.answer()
    query.message.reply_text(
        f"Great! We have lined up your message for broadcast. It wil be sent out within the next minute. Cya!"
    )

    data_to_write = (
        context.user_data['broadcast_target'],
        context.user_data['agency'],
        context.user_data['message']
    )

    # populate db with message
    con = sqlite3.connect(DB_NAME)
    cur = con.cursor()
    cur.execute(f"INSERT into {TABLE_MESSAGE} (kampong, agency, message) values (?, ?, ?);", data_to_write)
    con.commit()
    con.close()

    logger.info(f"Data written: {data_to_write}")

    return ConversationHandler.END


def cancel(update: Update, context: CallbackContext) -> int:
    """Cancels and ends the conversation."""
    user = update.message.from_user
    logger.info("User %s canceled the conversation.", user.first_name)
    update.message.reply_text(
        'Cya!', reply_markup=ReplyKeyboardRemove()
    )

    return ConversationHandler.END


psa_listener = ConversationHandler(
    entry_points=[CommandHandler('broadcast', broadcast)],
    states={
        SELECT_KAMPONG: [CallbackQueryHandler(draft_message)],
        ENTERED_MESSAGE: [MessageHandler(Filters.text & (~Filters.command), verify_message)],
        VERIFY_MESSAGE: [
            CallbackQueryHandler(
                confirm_message,
                pattern=f'^{MESSAGE_CONFIRMATION_POSITIVE}$'
            ),
            CallbackQueryHandler(
                edit_message,
                pattern=f'^{MESSAGE_CONFIRMATION_NEGATIVE}$'
            )
        ]
    },
    fallbacks=[CommandHandler('cancel', cancel)],
)

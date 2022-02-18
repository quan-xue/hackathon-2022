import logging
import sqlite3
import os
from sqlite3.dbapi2 import Cursor
from typing import Tuple, List

from telegram import ReplyKeyboardRemove, Update, InlineKeyboardButton, InlineKeyboardMarkup, ParseMode
from telegram.ext import (
    CommandHandler,
    MessageHandler,
    Filters,
    ConversationHandler,
    CallbackContext, CallbackQueryHandler
)


def start(update: Update, context: CallbackContext) -> int:
    """Starts the conversation"""
    update.message.reply_text(
        'Welcome to the *Kaypoh @ Kampong Concierge* 🤵‍♂. Here are the things I can do for you:\n'
        '1. /join to find your kampong telegram group\n'
        '2. /create_event to create an event for your kampong\n'
        '3. /search_event to search for events happening in your kampong\n',
        parse_mode=ParseMode.MARKDOWN
    ),

    return ConversationHandler.END


start_convo = ConversationHandler(
    entry_points=[CommandHandler('start', start)],
    states={
    },
    fallbacks=[CommandHandler('cancel', ConversationHandler.END)],
)

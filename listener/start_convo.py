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

# Enable logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO
)

logger = logging.getLogger(__name__)


def start(update: Update, context: CallbackContext) -> int:
    """Starts the conversation"""
    logger.info('user id %s', update.message.from_user.id)
    logger.info('chat id %s', update.message.chat_id)
    update.message.reply_text(
        'Welcome to the *Kaypoh @ Kampong Concierge* 🤵‍♂. Here are the things I can do for you:\n'
        '1. command 1\n'
        '2. command 2\n',
        parse_mode=ParseMode.MARKDOWN
    ),

    return ConversationHandler.END


start_convo = ConversationHandler(
    entry_points=[CommandHandler('start', start)],
    states={
    },
    fallbacks=[CommandHandler('cancel', ConversationHandler.END)],
)

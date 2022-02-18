#!/usr/bin/env python
# pylint: disable=C0116,W0613

"""
Bot for directing new joiners to their group
"""

import logging
import os
import sqlite3

from telegram import Update, ParseMode
from telegram.ext import (
    CallbackContext
)
from telegram.ext import Updater, CommandHandler
import sys
sys.path.append('../')
from listener.psa_listener import ALL_KAMPONGS

BOT_TOKEN = os.getenv('PSA_BROADCASTER_BOT_TOKEN')
BROADCAST_POLL_INTERVAL = 10  # in seconds

# Enable logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO
)

logger = logging.getLogger(__name__)


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


def broadcast_start(update: Update, context: CallbackContext):
    logger.info('Broadcast polling started.')
    kampong = 'Kolam Ayer'
    job_context = {
        'chat_id': update.message.chat_id,
        'kampong': kampong
    }
    logger.info(f"Kampong: {kampong}")

    context.job_queue.run_repeating(fetch_and_send, interval=BROADCAST_POLL_INTERVAL, context=job_context)


def main() -> None:
    """Run the bot."""
    # Create the Updater and pass it your bot's token.
    updater = Updater(BOT_TOKEN)

    # Get the dispatcher to register handlers
    dispatcher = updater.dispatcher

    # add psa broadcaster
    dispatcher.add_handler(CommandHandler('broadcast_start', broadcast_start))

    # Start the Bot
    updater.start_polling()

    # Run the bot until you press Ctrl-C or the process receives SIGINT,
    # SIGTERM or SIGABRT. This should be used most of the time, since
    # start_polling() is non-blocking and will stop the bot gracefully.
    updater.idle()


if __name__ == '__main__':
    main()

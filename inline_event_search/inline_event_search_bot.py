import os

from telegram import Update, ParseMode
from telegram.ext import Updater, CommandHandler, CallbackContext

import inline_event_search_service

BOT_TOKEN = os.getenv('INLINE_EVENT_BOT_TOKEN')

def main() -> None:
    """Run the bot."""
    # Create the Updater and pass it your bot's token.
    updater = Updater(BOT_TOKEN)

    # Get the dispatcher to register handlers
    dispatcher = updater.dispatcher


    # add event
    dispatcher.add_handler(inline_event_search_service.inline_event_search_handler())

    # Start the Bot
    updater.start_polling()

    # Run the bot until you press Ctrl-C or the process receives SIGINT,
    # SIGTERM or SIGABRT. This should be used most of the time, since
    # start_polling() is non-blocking and will stop the bot gracefully.
    updater.idle()


if __name__ == '__main__':
    main()

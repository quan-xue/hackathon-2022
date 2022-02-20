import os

from telegram import Update
from telegram.ext import Updater, CommandHandler, CallbackContext

import create_event_service
import inline_event_search_service
import search_event_service
from start_convo import start_convo
from matching import matching_convo
from psa_listener import psa_listener


BOT_TOKEN = os.getenv('CONCIERGE_BOT_TOKEN')


def help_command(update: Update, context: CallbackContext) -> None:
    """Displays info on how to use the bot."""
    update.message.reply_text("Welcome, welcome! Here are the things you can do:\n"
                              "1. Enter /join to find your kampong\n"
                              "2. Enter /create_event to create an event for your kampong.\n")


def main() -> None:
    """Run the bot."""
    # Create the Updater and pass it your bot's token.
    updater = Updater(BOT_TOKEN)

    # Get the dispatcher to register handlers
    dispatcher = updater.dispatcher

    # add start conversation - this is the default conversation when the bot is first started
    dispatcher.add_handler(start_convo)

    # add matching conversation
    dispatcher.add_handler(matching_convo)

    # add event
    dispatcher.add_handler(create_event_service.create_event_conv_handler(dispatcher))
    dispatcher.add_handler(search_event_service.search_event_conv_handler(dispatcher))
    dispatcher.add_handler(inline_event_search_service.inline_event_search_handler())

    # add psa
    dispatcher.add_handler(psa_listener)


    # add help
    dispatcher.add_handler(CommandHandler('help', help_command))

    # Start the Bot
    updater.start_polling()

    # Run the bot until you press Ctrl-C or the process receives SIGINT,
    # SIGTERM or SIGABRT. This should be used most of the time, since
    # start_polling() is non-blocking and will stop the bot gracefully.
    updater.idle()


if __name__ == '__main__':
    main()

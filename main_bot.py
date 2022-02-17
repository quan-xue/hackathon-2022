import os
import pandas as pd
from dotenv import load_dotenv
from telegram import Update
from telegram.ext import Updater, CommandHandler, CallbackContext

from matching import matching_convo
import create_event_service
import search_event_service

load_dotenv()

BOT_TOKEN = os.getenv('MATCH_BOT_TOKEN')


def help_command(update: Update, context: CallbackContext) -> None:
    """Displays info on how to use the bot."""
    update.message.reply_text("Type /join to find your kampong!")


def main() -> None:
    """Run the bot."""
    # Create the Updater and pass it your bot's token.
    updater = Updater(BOT_TOKEN)

    # Get the dispatcher to register handlers
    dispatcher = updater.dispatcher

    # add matching conversation
    dispatcher.add_handler(matching_convo)
    dispatcher.add_handler(create_event_service.create_event_conv_handler(dispatcher)),
    dispatcher.add_handler(search_event_service.search_event_conv_handler(dispatcher))
    dispatcher.add_handler(CommandHandler('help', help_command))

    # Start the Bot
    updater.start_polling()

    # Run the bot until you press Ctrl-C or the process receives SIGINT,
    # SIGTERM or SIGABRT. This should be used most of the time, since
    # start_polling() is non-blocking and will stop the bot gracefully.
    updater.idle()


if __name__ == '__main__':
    main()

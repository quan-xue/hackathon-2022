import os
import logging
from telegram import Update
from telegram.ext import CallbackContext, MessageHandler, Filters

# Enable logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO
)

logger = logging.getLogger(__name__)


def screen_message(update: Update, context: CallbackContext) -> None:
    """Echo the user message."""
    logger.info('Message text: %s', update.message.text)
    username = update.message.from_user.username
    message = f'@{username} sent the following offensive message: \n{update.message.text}'
    update.message.bot.send_message(int(os.getenv('MODERATOR_USERID')), message)


moderator = MessageHandler(Filters.text & ~Filters.command, screen_message)

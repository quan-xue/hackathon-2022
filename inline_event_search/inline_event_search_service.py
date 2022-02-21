import logging
from uuid import uuid4
import sys

from telegram import InlineQueryResultArticle, InputTextMessageContent, ParseMode, Update
from telegram.ext import Updater, InlineQueryHandler, CallbackContext
from telegram.utils.helpers import escape_markdown

sys.path.append('../')
from listener.util import format_event, is_valid_postal, search_events, search_postal

# Enable logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO
)
logger = logging.getLogger(__name__)

def inlinequery(update: Update, context: CallbackContext) -> None:
    """Handle the inline query."""
    query = update.inline_query.query

    logger.info(update.inline_query.query)

    if query == "":
        return
    
    if not is_valid_postal(query):
        logger.info(f"Invalid postal code value of {query}")
        return

    location = search_postal(query)
    if not location:
        logger.info(f"Cannot find address for {query}")
        return

    events = search_events(location, None)
    logger.info(
        f"query: {query}\n"
        f"result: {len(events)} events\n"
    )
    results = list(map(
        lambda event: InlineQueryResultArticle(
            id=str(uuid4()),
            title=event['name'],
            input_message_content=InputTextMessageContent(
                format_event(event),
                parse_mode=ParseMode.MARKDOWN
            )
        ), 
        events
    ))

    logger.info(f"results {results}")
    update.inline_query.answer(results)

def inline_event_search_handler():
    return InlineQueryHandler(inlinequery, pattern="^\d{6}$")

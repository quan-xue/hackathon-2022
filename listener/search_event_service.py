import logging

from dateutil import parser
from telegram import Update, ParseMode, ReplyKeyboardRemove
from telegram.ext import (
    Dispatcher,
    CommandHandler,
    MessageHandler,
    Filters,
    ConversationHandler,
    CallbackContext, 
)

from util import is_valid_postal, reverse_geocode, search_postal

# Enable logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO
)
logger = logging.getLogger(__name__)

GET_EVENT_DATE, GET_EVENT_LOCATION = range(2)

def start(update: Update, context: CallbackContext) -> int:
    update.message.reply_text(
        'Hi! To start finding your event, ' 
        'Please provide us with the *date of the event* which you are interested in. (e.g. 20/12/2021) \n',
        parse_mode=ParseMode.MARKDOWN
    )

    return GET_EVENT_DATE

def get_event_date(update: Update, context: CallbackContext) -> int:
    datetime_input = update.message.text

    try:
        datetime_obj = parser.parse(datetime_input)
    except:
        update.message.reply_text('Error in parsing the date and time, please try again. (e.g. 17/2/2021, 11:30pm)')
        return GET_EVENT_DATE
    
    context.user_data['time'] = datetime_obj
    update.message.reply_text(
        'Do you have any *preferred location* for the event?\n' 
        'You can use the Location pin drop function or key in the Postal Code. ' 
        'We will find the events that are close to that location.\n',
        parse_mode=ParseMode.MARKDOWN
        )
    return GET_EVENT_LOCATION

def get_event_location(update: Update, context: CallbackContext) -> int:
    event_location = update.message.location
    event_postal_code = update.message.text

    if event_location is not None:
        logger.info(f"Location of event is at {event_location.latitude}, {event_location.longitude}")
        location = reverse_geocode(event_location.latitude, event_location.longitude)
    elif event_postal_code is not None:
        logger.info(f"Postal of the event is at {event_postal_code}")
        if not is_valid_postal(event_postal_code):
            update.message.reply_text(
                f'Doesn\'t seem right leh... Must be *6-digit* (e.g. 123456) hor. You entered *{event_postal_code}*. Try again?',
                reply_markup=ReplyKeyboardRemove(),
                parse_mode=ParseMode.MARKDOWN
                )
            return GET_EVENT_LOCATION
        location = search_postal(event_postal_code)
        if not location:
            update.message.reply_text(f'🤔 Cannot find this address... You entered *{event_postal_code}*. Try again?',
                                    reply_markup=ReplyKeyboardRemove(),
                                    parse_mode=ParseMode.MARKDOWN)
            return GET_EVENT_LOCATION
    else:
        update.message.reply_text(
            'You have given us an invalid reply. Please either send your postal code or location pin.',
            parse_mode=ParseMode.MARKDOWN
            )
        return GET_EVENT_LOCATION

    context.user_data['location'] = location
    update.message.reply_text('Thanks for the input! Search for events based on your requirements.')
    update.message.reply_text('Here it is...')
    return ConversationHandler.END

def cancel(update: Update, context: CallbackContext) -> int:
    user = update.message.from_user
    logger.info("User %s canceled the conversation.", user.first_name)
    update.message.reply_text(
        'Bye! I hope we can talk again some day.', reply_markup=ReplyKeyboardRemove()
    )

    return ConversationHandler.END

def search_event_conv_handler(dispatcher: Dispatcher[CallbackContext, dict, dict, dict]) -> ConversationHandler:
    conv_handler = ConversationHandler(
        entry_points=[CommandHandler('search_event', start)],
        states={
            GET_EVENT_DATE: [MessageHandler(Filters.text & ~Filters.command, get_event_date)],
            GET_EVENT_LOCATION: [MessageHandler(Filters.location | Filters.text & (~Filters.command), get_event_location)]
        },
        fallbacks=[CommandHandler('cancel', cancel)],
    )
    return conv_handler

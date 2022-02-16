import logging
from dateutil import parser
from telegram import ReplyKeyboardRemove, Update, ParseMode, ReplyKeyboardMarkup
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

GET_EVENT_SERVICE, GET_INTEREST_GROUP, GET_LOCATION, GET_EVENT_NAME, GET_EVENT_DATETIME, GET_EVENT_END_DATETIME, GET_EVENT_DESC = range(7)


def start(update: Update, context: CallbackContext) -> int:
    reply_keyboard = [['1', '2']]

    update.message.reply_text(
        'Hi, which event service would you like to use?\n' 
        '1. Find events\n'
        '2. Create an event\n',
        reply_markup=ReplyKeyboardMarkup(
            reply_keyboard, one_time_keyboard=True, input_field_placeholder='1 or 2?'
        ),
    )

    return GET_EVENT_SERVICE


def get_event_service(update: Update, context: CallbackContext) -> int:
    event_service_type = update.message.text
    logger.info(f"The event service choosen is {event_service_type}.")

    if event_service_type == '1':
        update.message.reply_text(
            'Which group of events are you looking for?\n'
            '1. Events near a location\n'
            '2. Events by interest groups\n'
        )
        return GET_INTEREST_GROUP
    elif event_service_type == '2':
        update.message.reply_text(
            'Please provide us with the location of the event.\n'
            'You can use the Location pin drop function or key in the Postal Code.',
            parse_mode=ParseMode.MARKDOWN
        )
        return GET_LOCATION
    else:
        update.message.reply_text(
            'Oops, you are not sending the right input. Please choose from "1" or "2".', 
            parse_mode=ParseMode.MARKDOWN
            )
        return GET_EVENT_SERVICE


def get_location(update: Update, context: CallbackContext) -> int:
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
            return GET_LOCATION
        location = search_postal(event_postal_code)
        if not location:
            update.message.reply_text(f'🤔 Cannot find this address... You entered *{event_postal_code}*. Try again?',
                                    reply_markup=ReplyKeyboardRemove(),
                                    parse_mode=ParseMode.MARKDOWN)
            return GET_LOCATION
    else:
        update.message.reply_text(
            'You have given us an invalid reply. Please either send your postal code or location pin.',
            parse_mode=ParseMode.MARKDOWN
            )
        return GET_LOCATION

    logger.info(f"Location of event is at {location['address']}, {location['latitude']}, {location['longitude']}")
    update.message.reply_text(
        f'The location of your event is at {location["address"]}.\n'
        'Please key in **name of your event**.',
        parse_mode=ParseMode.MARKDOWN)
    
    context.user_data['location'] = location
    return GET_EVENT_NAME


def get_event_name(update: Update, context: CallbackContext) -> int:
    context.user_data['name'] = update.message.text

    update.message.reply_text('Please share the date and time of the event. (e.g. 17/2/2021, 11:30pm)')
    return GET_EVENT_DATETIME


def get_event_datetime(update: Update, context: CallbackContext) -> int:
    datetime_input = update.message.text
    datetime_obj = parser.parse(datetime_input)
    logger.info(f"Start datetime of event is at: {datetime_obj}")
    context.user_data['start_time'] = datetime_obj

    update.message.reply_text('Please key in the end date and time of your event')
    return GET_EVENT_END_DATETIME

def get_event_end_datetime(update: Update, context: CallbackContext) -> int:
    end_datetime = update.message.text
    datetime_obj = parser.parse(end_datetime)
    logger.info(f"End datetime of event is at: {datetime_obj}")
    context.user_data['end_time'] = datetime_obj

    update.message.reply_text('Please key in the description of your event.')
    return GET_EVENT_DESC

def get_event_desc(update: Update, context: CallbackContext) -> int:
    description = update.message.text
    context.user_data['description'] = description

    update.message.reply_text(
        'Please confirm the details of your event.'
        'If there are anything that you like to edit, please key in the associated number.' 
        'If not, please enter "confirm".\n\n'
        '*1. Name of the event:*\n'
        f'{context.user_data["name"]}\n'
        '*2. Location of the event:*\n'
        f'{context.user_data["location"]}\n'
        '*3. Start time of event:*\n'
        f'{context.user_data["start_time"]}\n'
        '*4. End time of event:*\n'
        f'{context.user_data["end_time"]}\n'
        '*5. Description of event:*\n'
        f'{context.user_data["description"]}\n',
        parse_mode=ParseMode.MARKDOWN
        )

def cancel(update: Update, context: CallbackContext) -> int:
    user = update.message.from_user
    logger.info("User %s canceled the conversation.", user.first_name)
    update.message.reply_text(
        'Bye! I hope we can talk again some day.', reply_markup=ReplyKeyboardRemove()
    )

    return ConversationHandler.END


def event_conv_handler(dispatcher: Dispatcher[CallbackContext, dict, dict, dict]) -> ConversationHandler:
    conv_handler = ConversationHandler(
        entry_points=[CommandHandler('event', start)],
        states={
            GET_EVENT_SERVICE: [MessageHandler(Filters.text & (~Filters.command), get_event_service)],
            GET_LOCATION: [
                MessageHandler(Filters.location | Filters.text & (~Filters.command), get_location),
            ],
            GET_EVENT_NAME: [MessageHandler(Filters.text & ~Filters.command, get_event_name)],
            GET_EVENT_DATETIME: [MessageHandler(Filters.text & ~Filters.command, get_event_datetime)],
            GET_EVENT_END_DATETIME: [MessageHandler(Filters.text & ~Filters.command, get_event_end_datetime)],
            GET_EVENT_DESC: [MessageHandler(Filters.text & ~Filters.command, get_event_desc)]
        },
        fallbacks=[CommandHandler('cancel', cancel)],
    )
    return conv_handler

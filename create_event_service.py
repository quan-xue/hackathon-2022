from datetime import datetime
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

GET_EVENT_NAME, GET_LOCATION, GET_EVENT_DATETIME, \
    GET_EVENT_END_DATETIME, GET_EVENT_DESC, GET_EVENT_CONFIRMATION_CHOICE = range(6)


def start(update: Update, context: CallbackContext) -> int:
    update.message.reply_text(
        'Hi! To start off the event creation process, ' 
        'you could first provide us with the name of the event.\n',
        parse_mode=ParseMode.MARKDOWN
    )

    return GET_EVENT_NAME

def is_editing_field(context: CallbackContext) -> bool:
    return 'is_editing' in context.user_data and context.user_data['is_editing']


def get_event_name(update: Update, context: CallbackContext) -> int:
    context.user_data['name'] = update.message.text

    if is_editing_field(context):
        update.message.reply_text(event_summary(context), parse_mode=ParseMode.MARKDOWN)
        return GET_EVENT_CONFIRMATION_CHOICE

    update.message.reply_text(
        'Please provide us with the location of the event.\n'
        'You can use the Location pin drop function or key in the Postal Code.',
        parse_mode=ParseMode.MARKDOWN
    )
    return GET_LOCATION


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

    context.user_data['location'] = location
    if is_editing_field(context):
        update.message.reply_text(event_summary(context), parse_mode=ParseMode.MARKDOWN)
        return GET_EVENT_CONFIRMATION_CHOICE

    update.message.reply_text(
        f'The location of your event is at {location["address"]}.\n'
        'Please share starting time of the event. (e.g. 17/2/2021, 11:30pm)'
        )
    return GET_EVENT_DATETIME


def get_event_datetime(update: Update, context: CallbackContext) -> int:
    datetime_input = update.message.text
    try:
        datetime_obj = parser.parse(datetime_input)
    except:
        update.message.reply_text('Error in parsing the date and time, please try again. (e.g. 17/2/2021, 11:30pm)')
        return GET_EVENT_DATETIME

    if datetime_obj <= datetime.now():
        update.message.reply_text("Starting time of event has to be in the future. Please enter start time of event again.")
        return GET_EVENT_DATETIME
    
    if 'end_time' in context.user_data and datetime_obj >= context.user_data['end_time']:
        update.message.reply_text("Starting time of event cannot be after the ending time of the event. Please enter start time of event again.")
        return GET_EVENT_DATETIME

    logger.info(f"Start datetime of event is at: {datetime_obj}")
    context.user_data['start_time'] = datetime_obj

    if is_editing_field(context):
        update.message.reply_text(event_summary(context), parse_mode=ParseMode.MARKDOWN)
        return GET_EVENT_CONFIRMATION_CHOICE

    update.message.reply_text('Please key in the ending time of your event.')
    return GET_EVENT_END_DATETIME

def get_event_end_datetime(update: Update, context: CallbackContext) -> int:
    end_datetime = update.message.text
    try:
        datetime_obj = parser.parse(end_datetime)
    except:
        update.message.reply_text('Error in parsing the date and time, please try again. (e.g. 17/2/2021, 11:30pm)')
        return GET_EVENT_END_DATETIME

    if datetime_obj <= context.user_data['start_time']:
        update.message.reply_text(
            f"The ending time of event cannot be earlier than the start time of the event. Please enter end time of event again."
            )
        return GET_EVENT_END_DATETIME

    logger.info(f"End datetime of event is at: {datetime_obj}")
    context.user_data['end_time'] = datetime_obj

    if is_editing_field(context):
        update.message.reply_text(event_summary(context), parse_mode=ParseMode.MARKDOWN)
        return GET_EVENT_CONFIRMATION_CHOICE

    update.message.reply_text('Please key in the description of your event.')
    return GET_EVENT_DESC

def event_summary(context: CallbackContext) -> str:
    return (
        'Please confirm the details of your event. '
        'If there are anything that you like to edit, please key in the associated number.\n' 
        'If not, please enter "confirm".\n\n'
        '*1. Name of the event:*\n'
        f'{context.user_data["name"]}\n\n'
        '*2. Location of the event:*\n'
        f'{context.user_data["location"]["address"]}\n\n'
        '*3. Start time of event:*\n'
        f'{context.user_data["start_time"]}\n\n'
        '*4. End time of event:*\n'
        f'{context.user_data["end_time"]}\n\n'
        '*5. Description of event:*\n'
        f'{context.user_data["description"]}\n\n'
    )

def get_event_desc(update: Update, context: CallbackContext) -> int:
    description = update.message.text
    context.user_data['description'] = description

    if is_editing_field(context):
        update.message.reply_text(event_summary(context), parse_mode=ParseMode.MARKDOWN)
        return GET_EVENT_CONFIRMATION_CHOICE

    update.message.reply_text(
        event_summary(context),
        parse_mode=ParseMode.MARKDOWN
    )
    return GET_EVENT_CONFIRMATION_CHOICE

def get_event_confirmation(update: Update, context: CallbackContext) -> int:
    decision = update.message.text

    if decision == "confirm":
        # save context.user_data into db
        update.message.reply_text(
            'Your event has been created!'
        )
        return ConversationHandler.END


    context.user_data['is_editing'] = True
    if decision == '1':
        update.message.reply_text('Please key in the new event name.')
        return GET_EVENT_NAME
    elif decision == '2':
        update.message.reply_text('Please key in the new location. Either through location pin or postal code.')
        return GET_LOCATION
    elif decision == '3':
        update.message.reply_text('Please key in the new event date time.')
        return GET_EVENT_DATETIME
    elif decision == '4':
        update.message.reply_text('Please key in the date time in which the event would end.')
        return GET_EVENT_END_DATETIME
    elif decision == '5':
        update.message.reply_text('Please key in the description of the event.')
        return GET_EVENT_DESC
    else:
        context.user_data['is_editing'] = False
        update.message.reply_text(
            'Invalid input.\n'
            'Either enter "confirm" to confirm the event.\n'
            'Or pick the number associated to the input that you would like to edit.\n'
        )
        return GET_EVENT_CONFIRMATION_CHOICE


def cancel(update: Update, context: CallbackContext) -> int:
    user = update.message.from_user
    logger.info("User %s canceled the conversation.", user.first_name)
    update.message.reply_text(
        'Bye! I hope we can talk again some day.', reply_markup=ReplyKeyboardRemove()
    )

    return ConversationHandler.END


def event_conv_handler(dispatcher: Dispatcher[CallbackContext, dict, dict, dict]) -> ConversationHandler:
    conv_handler = ConversationHandler(
        entry_points=[CommandHandler('create_event', start)],
        states={
            GET_EVENT_NAME: [MessageHandler(Filters.text & ~Filters.command, get_event_name)],
            GET_LOCATION: [
                MessageHandler(Filters.location | Filters.text & (~Filters.command), get_location),
            ],
            GET_EVENT_DATETIME: [MessageHandler(Filters.text & ~Filters.command, get_event_datetime)],
            GET_EVENT_END_DATETIME: [MessageHandler(Filters.text & ~Filters.command, get_event_end_datetime)],
            GET_EVENT_DESC: [MessageHandler(Filters.text & ~Filters.command, get_event_desc)],
            GET_EVENT_CONFIRMATION_CHOICE: [MessageHandler(Filters.text & ~Filters.command, get_event_confirmation)]
        },
        fallbacks=[CommandHandler('cancel', cancel)],
    )
    return conv_handler

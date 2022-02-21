from datetime import datetime
import logging
import requests
from telegram import ReplyKeyboardRemove, Update, ParseMode
from telegram.ext import (
    Dispatcher,
    CommandHandler,
    MessageHandler,
    Filters,
    ConversationHandler,
    CallbackContext, 
)

from util import format_datetime, is_valid_postal, parse_date, reverse_geocode, search_postal


# Enable logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO
)
logger = logging.getLogger(__name__)

GET_EVENT_NAME, GET_LOCATION, GET_EVENT_DATETIME, \
    GET_EVENT_END_DATETIME, GET_EVENT_DESC, GET_EVENT_CONFIRMATION_CHOICE = range(6)

DATETIME_FORMAT_HELPER = '(Enter DD/MM/YYYY HH:MM e.g. 31/03/2022 16:30)'
CANCEL_PROCESS = 'Enter /cancel to end.'


def start(update: Update, context: CallbackContext) -> int:
    update.message.reply_text(
        f'Alrighty! Let\'s get started. What would you like to *name* your event? {CANCEL_PROCESS}',
        parse_mode=ParseMode.MARKDOWN
    )

    return GET_EVENT_NAME


def is_editing_field(context: CallbackContext) -> bool:
    return 'is_editing' in context.chat_data and context.chat_data['is_editing']


def get_event_name(update: Update, context: CallbackContext) -> int:
    context.chat_data['name'] = update.message.text

    if is_editing_field(context):
        update.message.reply_text(event_summary(update, update, context), parse_mode=ParseMode.MARKDOWN)
        return GET_EVENT_CONFIRMATION_CHOICE

    update.message.reply_text(
        'Please provide us with the *location* of the event.\n'
        'You can key in the postal code (6-digit e.g. 123456) or if you are using a phone, use the location pin drop.\n'
        f'{CANCEL_PROCESS}',
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
                f'Doesn\'t seem right leh... Must be *6-digit* (e.g. 123456) hor. You entered *{event_postal_code}*. '
                f'Try again?\n{CANCEL_PROCESS}',
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
            'Don\'t get it... Please either enter your postal code (e.g. 123456) '
            f'or send a location pin if on your phone.\n{CANCEL_PROCESS}',
            parse_mode=ParseMode.MARKDOWN
            )
        return GET_LOCATION

    context.chat_data['location'] = location
    if is_editing_field(context):
        update.message.reply_text(event_summary(update, context), parse_mode=ParseMode.MARKDOWN)
        return GET_EVENT_CONFIRMATION_CHOICE

    update.message.reply_text(
        f'Sweet! The *location* of your event will be at {location["address"]} 😎.\n\n'
        f'When will the event *start*? {DATETIME_FORMAT_HELPER}\n{CANCEL_PROCESS}',
        parse_mode=ParseMode.MARKDOWN
        )
    return GET_EVENT_DATETIME


def get_event_datetime(update: Update, context: CallbackContext) -> int:
    datetime_input = update.message.text
    try:
        datetime_obj = parse_date(datetime_input)
    except:
        update.message.reply_text(f'Hmm... Cannot figure out your time leh 🤔 You entered *{datetime_input}*'
                                  f'{DATETIME_FORMAT_HELPER}\n{CANCEL_PROCESS}')
        return GET_EVENT_DATETIME

    if datetime_obj <= datetime.now():
        update.message.reply_text(f"Don'\t look back in anger...Starting time of event has to be in the future! "
                                  f"You entered *{datetime_input}*. {DATETIME_FORMAT_HELPER}\n{CANCEL_PROCESS}")
        return GET_EVENT_DATETIME
    
    if 'end_time' in context.chat_data and datetime_obj >= context.chat_data['end_time']:
        update.message.reply_text(f"Well... Don\'t end your event before it has even started! "
                                  f"Your start time is *{datetime_input}* but your end time "
                                  f"is *{context.chat_data['end_time']}*"
                                  f"Please enter a new *start time*. {DATETIME_FORMAT_HELPER}\n{CANCEL_PROCESS}")
        return GET_EVENT_DATETIME

    logger.info(f"Start datetime of event is at: {datetime_obj}")
    context.chat_data['start_time'] = datetime_obj

    if is_editing_field(context):
        update.message.reply_text(event_summary(update, context), parse_mode=ParseMode.MARKDOWN)
        return GET_EVENT_CONFIRMATION_CHOICE

    update.message.reply_text(
        f'All good things must come to an end. 😢 When should your event *end*? {DATETIME_FORMAT_HELPER}\n{CANCEL_PROCESS}',
        parse_mode=ParseMode.MARKDOWN
    )
    return GET_EVENT_END_DATETIME


def get_event_end_datetime(update: Update, context: CallbackContext) -> int:
    end_datetime = update.message.text
    try:
        datetime_obj = parse_date(end_datetime)
    except:
        update.message.reply_text(f'Sorry can\'t figure out what you meant...{DATETIME_FORMAT_HELPER}\n{CANCEL_PROCESS}')
        return GET_EVENT_END_DATETIME

    if datetime_obj <= context.chat_data['start_time']:
        update.message.reply_text(
            "Well... Don\'t end your event before it has even started! "
            f"Your end time is {end_datetime} but your start time is {context.chat_data['start_time']}"
            f"Please enter a new end time. {DATETIME_FORMAT_HELPER}\n{CANCEL_PROCESS}"
            )
        return GET_EVENT_END_DATETIME

    logger.info(f"End datetime of event is at: {datetime_obj}")
    context.chat_data['end_time'] = datetime_obj

    if is_editing_field(context):
        update.message.reply_text(event_summary(update, context), parse_mode=ParseMode.MARKDOWN)
        return GET_EVENT_CONFIRMATION_CHOICE

    update.message.reply_text(
        f'Almost there! Finally, enter a description for your event.\n{CANCEL_PROCESS}',
        parse_mode=ParseMode.MARKDOWN
    )
    return GET_EVENT_DESC


def event_summary(update: Update, context: CallbackContext) -> str:
    return (
        'Swee la, let\'s double-confirm the details of your event. \n'
        'If there is anything that you would like to *edit*, please enter the number of the item ie. *1* to *5*.\n' 
        f'If not, please enter "*confirm*".\n{CANCEL_PROCESS}\n\n'
        '*1. Name of the event:*\n'
        f'{context.chat_data["name"]}\n\n'
        '*2. Location of the event:*\n'
        f'{context.chat_data["location"]["address"]}\n\n'
        '*3. Start time of event:*\n'
        f'{format_datetime(context.chat_data["start_time"])}\n\n'
        '*4. End time of event:*\n'
        f'{format_datetime(context.chat_data["end_time"])}\n\n'
        '*5. Description of event:*\n'
        f'{context.chat_data["description"]}\n\n'
        '*Organizer:*\n'
        f'@{update.effective_user.username}\n\n'
    )


def get_event_desc(update: Update, context: CallbackContext) -> int:
    description = update.message.text
    context.chat_data['description'] = description

    if is_editing_field(context):
        update.message.reply_text(event_summary(update, context), parse_mode=ParseMode.MARKDOWN)
        return GET_EVENT_CONFIRMATION_CHOICE

    update.message.reply_text(
        event_summary(update, context),
        parse_mode=ParseMode.MARKDOWN
    )
    return GET_EVENT_CONFIRMATION_CHOICE


def get_event_confirmation(update: Update, context: CallbackContext) -> int:
    decision = update.message.text
    if decision == "confirm":
        # save context.chat_data into db
        data = {
            'new_events': {
                "start_time": context.chat_data['start_time'].strftime('%Y-%m-%dT%H:%M:%S.%fZ'),	
                "end_time": context.chat_data['end_time'].strftime('%Y-%m-%dT%H:%M:%S.%fZ'),
                'name': context.chat_data['name'],
                'category': 'independent',
                'description': context.chat_data['description'],
                'lng': float(context.chat_data["location"]["longitude"]),
                'lat': float(context.chat_data["location"]["latitude"]),
                'address': context.chat_data["location"]["address"],
                'organizer': update.effective_user.username
            },
        }
        logger.info(f"data: {data}")
        requests.post("http://server:8000/api/events/", json=data)
        update.message.reply_text(
            'Your event has been created!'
        )
        return ConversationHandler.END

    context.chat_data['is_editing'] = True
    if decision == '1':
        update.message.reply_text('Please key in the new event name.')
        return GET_EVENT_NAME
    elif decision == '2':
        update.message.reply_text('Please key in the new location. Either through location pin or postal code.')
        return GET_LOCATION
    elif decision == '3':
        update.message.reply_text(f'Please key in the new event date time {DATETIME_FORMAT_HELPER}')
        return GET_EVENT_DATETIME
    elif decision == '4':
        update.message.reply_text(f'Please key in the date time in which the event would end {DATETIME_FORMAT_HELPER}.')
        return GET_EVENT_END_DATETIME
    elif decision == '5':
        update.message.reply_text('Please key in the description of the event.')
        return GET_EVENT_DESC
    else:
        context.chat_data['is_editing'] = False
        update.message.reply_text(
            'Invalid input.\n'
            'Either enter "confirm" to confirm the event.\n'
            'Or pick a number to edit the field.\n'
        )
        return GET_EVENT_CONFIRMATION_CHOICE


def cancel(update: Update, context: CallbackContext) -> int:
    user = update.message.from_user
    logger.info("User %s canceled the conversation.", user.first_name)
    update.message.reply_text(
        'Bye! I hope we can talk again some day.', reply_markup=ReplyKeyboardRemove()
    )

    return ConversationHandler.END


def create_event_conv_handler(dispatcher: Dispatcher[CallbackContext, dict, dict, dict]) -> ConversationHandler:
    conv_handler = ConversationHandler(
        entry_points=[CommandHandler('createevent', start)],
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

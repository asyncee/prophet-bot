import datetime as dt
import logging
import os

import dotenv
from telegram.ext import CommandHandler
from telegram.ext import MessageHandler, Filters
from telegram.ext import Updater

from exact_time import extractor

dotenv.load_dotenv(dotenv.find_dotenv())

logging.basicConfig(
    level=logging.DEBUG, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)

logger = logging.getLogger(__name__)

updater = Updater(token=os.environ["TOKEN"])
dispatcher = updater.dispatcher


unrecognized_phrases = set()


def error(bot, update, error):
    logger.warning('Update "%s" caused error "%s"' % (update, error))


def start(bot, update):
    bot.send_message(
        chat_id=update.message.chat_id,
        text="""
        Привет! Я напоминалка! Напиши мне, о чём тебе стоит напомнить простой строкой, например,
        "сходить в магазин завтра в 10:30"
        """,
    )


def is_today(moment):
    return dt.datetime.today().date() == moment.date()


def is_tomorrow(moment):
    return dt.datetime.today().date() + dt.timedelta(days=1) == moment.date()


def is_day_after_tomorrow(moment):
    return dt.datetime.today().date() + dt.timedelta(days=2) == moment.date()


def is_on_this_week(moment):
    start = moment - dt.timedelta(days=moment.weekday())
    return start <= moment <= start + dt.timedelta(days=7)


def human_format_dayofweek(moment):
    return moment.strftime("%A")


def human_format_date(moment):
    return moment.strftime("%d %B %Y")


def human_format(moment):
    if moment.minute:
        time = f"в {moment.hour}:{moment.minute}"
    else:
        time = f"в {moment.hour}"

    if is_today(moment):
        date = "сегодня"
    elif is_tomorrow(moment):
        date = "завтра"
    elif is_day_after_tomorrow(moment):
        date = f"послезавтра ({human_format_dayofweek(moment)})"
    elif is_on_this_week(moment):
        date = f"в эту {human_format_dayofweek(moment)}"
    else:
        date = human_format_date(moment)

    return f"{date} {time}"


def print_exact_time(bot, update):
    global unrecognized_phrases
    extract = extractor(update.message.text)

    if extract is None:
        unrecognized_phrases.add(update.message.text)
        text = "Я ничего не поняла."
    else:
        when = human_format(extract.time)
        text = f"""
        "{extract.task}" — напомню {when} ({extract.time.strftime('%Y-%m-%d %H:%M')})
        """

    bot.send_message(chat_id=update.message.chat_id, text=text)


def print_unrecognized_phrases(bot, update):
    global unrecognized_phrases
    text = ", ".join(unrecognized_phrases)
    bot.send_message(chat_id=update.message.chat_id, text=text)


def print_timezone(bot, update):
    tz = dt.datetime.now(dt.timezone.utc).astimezone().tzname()
    bot.send_message(chat_id=update.message.chat_id, text=tz)


def unknown(bot, update):
    bot.send_message(
        chat_id=update.message.chat_id, text="Sorry, I didn't understand that command."
    )


exact_time_handler = MessageHandler(Filters.text, print_exact_time)
dispatcher.add_handler(exact_time_handler)

unrecognized_handler = CommandHandler("print", print_unrecognized_phrases)
dispatcher.add_handler(unrecognized_handler)

tz_handler = CommandHandler("timezone", print_timezone)
dispatcher.add_handler(tz_handler)

start_handler = CommandHandler("start", start)
dispatcher.add_handler(start_handler)

unknown_handler = MessageHandler(Filters.command, unknown)
dispatcher.add_handler(unknown_handler)

dispatcher.add_error_handler(error)

updater.start_polling()
updater.idle()

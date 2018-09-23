import datetime as dt
import logging
import os

import dotenv
from telegram.ext import CommandHandler, StringCommandHandler
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
        text='Напишите, о чем вам напомнить. Соощение может быть вида: "забрать посылку завтра в 10".'
    )


def print_exact_time(bot, update):
    global unrecognized_phrases
    extract = extractor(update.message.text)

    if extract is None:
        unrecognized_phrases.add(update.message.text)
        text = 'Я ничего не поняла.'
    else:
        text = f"""
        "{extract.task}" — напомню "{extract.time_string}" ({extract.time.strftime('%Y-%m-%d %H:%M')})
        """

    bot.send_message(chat_id=update.message.chat_id, text=text)


def print_unrecognized_phrases(bot, update):
    global unrecognized_phrases
    text = ', '.join(unrecognized_phrases)
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

import logging
import os

import dotenv
from telegram.ext import CommandHandler
from telegram.ext import MessageHandler, Filters
from telegram.ext import Updater

dotenv.load_dotenv(dotenv.find_dotenv())

logging.basicConfig(
    level=logging.DEBUG, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)

logger = logging.getLogger(__name__)

updater = Updater(token=os.environ["TOKEN"])
dispatcher = updater.dispatcher


def error(bot, update, error):
    logger.warning('Update "%s" caused error "%s"' % (update, error))


def start(bot, update):
    bot.send_message(chat_id=update.message.chat_id, text="I'm a bot, please talk to me!")


def echo(bot, update):
    bot.send_message(chat_id=update.message.chat_id, text=update.message.text)


def unknown(bot, update):
    bot.send_message(
        chat_id=update.message.chat_id, text="Sorry, I didn't understand that command."
    )


echo_handler = MessageHandler(Filters.text, echo)
dispatcher.add_handler(echo_handler)


start_handler = CommandHandler("start", start)
dispatcher.add_handler(start_handler)

unknown_handler = MessageHandler(Filters.command, unknown)
dispatcher.add_handler(unknown_handler)

dispatcher.add_error_handler(error)

updater.start_polling()
updater.idle()

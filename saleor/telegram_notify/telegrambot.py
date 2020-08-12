import logging
from typing import List

import telegram
from telegram.ext import CommandHandler
from django_telegrambot.apps import DjangoTelegramBot

from saleor.telegram_notify.plugin import TelegramOrderNotifyPlugin

from saleor.telegram_notify.models import Chat

logger = logging.getLogger(__name__)


def start(bot: telegram.Bot, update: telegram.Update):
    allowed_usernames = TelegramOrderNotifyPlugin.get_allowed_usernames()
    telegram_user = update.effective_user

    if telegram_user.username not in allowed_usernames:
        bot.send_message(
            update.message.chat_id,
            text='Простите! У вас нету прав для получения увдомлений с этого бота. '
                 'Если это ошибка обратитесь администратору магазина.')
        return

    try:
        Chat.objects.get(chat_id=update.message.chat_id)
    except Chat.DoesNotExist:
        Chat.objects.create(chat_id=update.message.chat_id,
                            username=telegram_user.username)
        logger.info(f"Authorized user: chat_id: {update.message.chat_id}")

        bot.send_message(
            update.message.chat_id,
            text=f'Здравствуйте, @{telegram_user.username}! '
                 f'Вы успешно активированы для получения уведомлений о заказов магазина.')
    else:
        bot.send_message(
            update.message.chat_id,
            text=f'Здравствуйте, @{telegram_user.username}! '
                 f'Вы уже зарегистрированы для уведомлений о заказов магазина.')


def main():
    logger.info("Loading handlers for telegram bot")
    dp = DjangoTelegramBot.dispatcher

    dp.add_handler(CommandHandler("start", start))
    dp.add_handler(CommandHandler("help", start))

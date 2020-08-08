import telegram
from django.contrib.auth import get_user_model
from django.utils import timezone
from telegram.ext import CommandHandler, MessageHandler, Filters
from django_telegrambot.apps import DjangoTelegramBot

import logging

from saleor.telegram_notify.models import Chat, ChatStates
from saleor.telegram_notify.tasks import send_bot_confirm_code
from saleor.telegram_notify.utils import state_validator

User = get_user_model()
logger = logging.getLogger(__name__)
RESEND_CONFIRM_CODE = 'Отправить код повторно'


@state_validator(allow_state=ChatStates.undefined)
def start(bot: telegram.Bot, update: telegram.Update, chat: Chat = None):
    bot.send_message(
        update.message.chat_id,
        text='Авторизуетесь чтобы начать получать уведомления о заказов с магазина.')
    bot.send_message(
        update.message.chat_id,
        text='Введите вашу почту, который зарегестрирован в административной панели:')
    chat.state = ChatStates.waiting_for_email
    chat.save()


@state_validator(allow_state=ChatStates.waiting_for_email)
def handle_email(bot: telegram.Bot, update: telegram.Update, chat: Chat):
    try:
        user = User.objects.get(email=update.message.text, is_staff=True)
    except User.DoesNotExist:
        bot.send_message(
            chat_id=update.message.chat_id,
            text="Администратор с такой почтой не существует!")
    else:
        chat.user = user
        chat.state = ChatStates.user_is_not_confirmed
        chat.last_code_send_time = timezone.now()
        chat.save()
        send_bot_confirm_code.delay(chat.confirm_code, chat.user.email)

        bot.send_message(
            chat_id=update.message.chat_id,
            text="Посмотрите почту, мы отправили код для подтверждения. " +
                 "Отправленный код актуален до конца дня.")
        bot.send_message(
            chat_id=update.message.chat_id,
            text="Повторная отправка кода доступна после 5 мин с текущего времени.")
        bot.send_message(
            chat_id=update.message.chat_id,
            text="Введите код подтверждения",
            reply_markup=telegram.ReplyKeyboardMarkup(
                keyboard=[[RESEND_CONFIRM_CODE]],
                resize_keyboard=True
            ))


@state_validator(allow_state=ChatStates.user_is_not_confirmed)
def resend_confirm_code(bot: telegram.Bot, update: telegram.Update, chat: Chat):
    now = timezone.now()
    available_time_for_resend_code = chat.last_code_send_time + timezone.timedelta(
        minutes=Chat.RESEND_CODE_AVAILABLE_AFTER_MINUTES)

    if now < available_time_for_resend_code:
        time = available_time_for_resend_code - now
        minutes = int(time.seconds / 60)
        bot.send_message(
            chat_id=chat.chat_id,
            text=f'Повторная отправка кода не доступна в течении {minutes} минут.'
                 f'Повторите позже!')
        return

    chat.regenerate_confirm_code()
    chat.last_code_send_time = timezone.now()
    chat.save()
    send_bot_confirm_code.delay(chat.confirm_code, chat.user.email)

    bot.send_message(
        chat_id=update.message.chat_id,
        text="Посмотрите почту мы отправили код для подтверждения. "
             "Отправленный код актуален до конца дня.")
    bot.send_message(
        chat_id=update.message.chat_id,
        text=f"Повторная отправка кода доступна после "
             f"{Chat.RESEND_CODE_AVAILABLE_AFTER_MINUTES} мин с текущего времени.")
    bot.send_message(
        chat_id=update.message.chat_id,
        text="Введите код подтверждения")


@state_validator(allow_state=ChatStates.user_is_not_confirmed)
def handle_confirm_code(bot: telegram.Bot, update: telegram.Update, chat: Chat):
    if update.message.text != chat.confirm_code:
        bot.send_message(chat_id=chat.chat_id, text='Не правильный код подтверждения!')
        return

    chat.state = ChatStates.authorized_admin
    chat.save()
    bot.send_message(chat_id=chat.chat_id,
                     text='Вы успешно авторизованы!',
                     reply_markup=telegram.ReplyKeyboardRemove()
                     )


def logout(bot: telegram.bot, update: telegram.Update):
    Chat.objects.filter(chat_id=update.message.chat_id).delete()

    bot.send_message(chat_id=update.message.chat_id,
                     text='Вы успешно вышли!',
                     reply_markup=telegram.ReplyKeyboardRemove()
                     )


def main():
    logger.info("Loading handlers for telegram bot")

    dp = DjangoTelegramBot.dispatcher

    dp.add_handler(CommandHandler("start", start))
    dp.add_handler(CommandHandler("quit", logout))
    dp.add_handler((MessageHandler(Filters.regex(r'^\S+@\S+$'), handle_email)))
    dp.add_handler(MessageHandler(Filters.regex(RESEND_CONFIRM_CODE),
                                  resend_confirm_code))
    dp.add_handler(MessageHandler(Filters.regex(r'^[a-z]+$'), handle_confirm_code))

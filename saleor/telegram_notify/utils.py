from typing import Callable

import telegram
from django.utils import timezone

from saleor.telegram_notify.models import ChatStates, Chat


def state_validator(allow_state: str) -> Callable[[Callable], Callable]:
    def decorator(
            func: Callable[[telegram.Bot, telegram.Update, Chat], None])\
            -> Callable[[telegram.Bot, telegram.Update], None]:
        def wrapper(bot: telegram.Bot, update: telegram.Update) -> None:
            chat, _created = Chat.objects.get_or_create(chat_id=update.message.chat_id)

            if allow_state == ChatStates.undefined:
                bot.send_message(chat_id=chat.chat_id, text='Бот запущен!')
                if chat.state != ChatStates.undefined:
                    return

            if allow_state == ChatStates.waiting_for_email:
                if chat.state != allow_state:
                    bot.send_message(
                        chat_id=chat.chat_id,
                        text='Простите, я не умею понимать или расказать шутку!')
                    return

            if allow_state == ChatStates.user_is_not_confirmed:
                if chat.state != allow_state or not chat.user_id:
                    bot.send_message('Привет)!')
                    return

                now = timezone.now()
                if not chat.last_code_send_time or \
                        now.date() != chat.last_code_send_time.date():
                    bot.send_message(chat_id=chat.chat_id, text='Код уже устарел!')
                    return

            if allow_state == ChatStates.authorized_admin:
                if chat.state != allow_state:
                    bot.send_message('Привет)!')
                    return

            func(bot, update, chat)

        return wrapper

    return decorator

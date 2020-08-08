import telegram
from django_telegrambot.apps import DjangoTelegramBot

from saleor.celeryconf import app
from saleor.order.models import Order, OrderLine
from saleor.telegram_notify.models import Chat, ChatStates


@app.task
def telegram_order_create_notify(order_id: int):
    order = Order.objects.get(id=order_id)
    text = get_order_check(order)
    bot = DjangoTelegramBot.getBot()
    for chat in Chat.objects.filter(state=ChatStates.authorized_admin):
        bot.send_message(chat_id=chat.chat_id,
                         text=text,
                         parse_mode=telegram.ParseMode.HTML)


@app.task
def telegram_order_canceled_notify(order_id: int):
    text = f'Заказ #{order_id} отклонен.'
    bot = DjangoTelegramBot.getBot()

    for chat in Chat.objects.filter(state=ChatStates.authorized_admin):
        bot.send_message(chat_id=chat.chat_id,
                         text=text)


@app.task
def telegram_order_fully_paid_notify(order_id: int) -> None:
    text = f'Заказ #{order_id} полностью оплачен.'
    bot = DjangoTelegramBot.getBot()

    for chat in Chat.objects.filter(state=ChatStates.authorized_admin):
        bot.send_message(chat_id=chat.chat_id,
                         text=text)


@app.task
def telegram_order_fulfilled_notify(order_id: int):
    text = f'Заказ #{order_id} выполнен.'
    bot = DjangoTelegramBot.getBot()

    for chat in Chat.objects.filter(state=ChatStates.authorized_admin):
        print(chat.chat_id)
        bot.send_message(chat_id=chat.chat_id, text=text)


def get_order_check(order: "Order") -> str:
    message = f'<b>Новый заказ</b>: #{order.id}\n' \
              f'<b>ФИО</b>: {order.user.get_full_name()}\n' \
              f'<b>Тел</b>: {order.billing_address.phone}\n' \
              f'<b>E-mail</b>: {order.user_email}\n' \
              f'<b>Город</b>: {order.billing_address.city}\n' \
              f'<b>Аддресс</b>: {order.billing_address.street_address_1}\n' \
              f'\n<b>Товары</b>:\n' \
              f'---------------\n'

    for line in order.lines.all():
        message += get_product_info(line)
        message += f'-' * 15

    return message


def get_product_info(line: "OrderLine") -> str:
    body = f'<b>Название</b>: {line.product_name}\n' \
           f'<b>Вариант</b>: {line.variant_name}\n' \
           f'<b>Количество</b>: {line.quantity}\n' \
           f'<b>Цена за единицу</b>: {line.variant.price}\n' \
           f'<b>Общее</b>: {line.get_total()}\n'

    return body

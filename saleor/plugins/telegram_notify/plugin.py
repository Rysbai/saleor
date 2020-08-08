from typing import Any, TYPE_CHECKING

from saleor.plugins.base_plugin import BasePlugin
from .tasks import (
    telegram_order_create_notify, telegram_order_canceled_notify,
    telegram_order_fulfilled_notify, telegram_order_fully_paid_notify
)

if TYPE_CHECKING:
    from saleor.order.models import Order


class TelegramOrderNotifyPlugin(BasePlugin):
    PLUGIN_ID = "saleor.plugins.telegram_notify"
    PLUGIN_NAME = "Telegram Bot"
    PLUGIN_DESCRIPTION = "Уведомляет подписанных администраторов " \
                         "о новых, измененных, отмененных и выполненный заказов."
    DEFAULT_ACTIVE = True

    def order_created(self, order: "Order", previous_value: Any):
        telegram_order_create_notify.delay(order.id)

    def order_fulfilled(self, order: "Order", previous_value: Any) -> Any:
        telegram_order_fulfilled_notify.delay(order.id)

    def order_cancelled(self, order: "Order", previous_value: Any) -> Any:
        telegram_order_canceled_notify.delay(order.id)

    def order_fully_paid(self, order: "Order", previous_value: Any) -> Any:
        telegram_order_fully_paid_notify.delay(order.id)

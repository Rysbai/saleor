from typing import Any, TYPE_CHECKING

from saleor.plugins.base_plugin import BasePlugin, ConfigurationTypeField
from .tasks import (
    telegram_order_create_notify, telegram_order_canceled_notify,
    telegram_order_fulfilled_notify, telegram_order_fully_paid_notify
)
from ..plugins.models import PluginConfiguration

if TYPE_CHECKING:
    from saleor.order.models import Order


class TelegramOrderNotifyPlugin(BasePlugin):
    class ConfNames:
        admin_telegram_usernames = 'admin_telegram_usernames'
        notify_order_created = 'notify_order_created'
        notify_order_fulfilled = 'notify_order_fulfilled'
        notify_order_canceled = 'notify_order_canceled'
        notify_order_fully_paid = 'notify_order_fully_paid'

    PLUGIN_ID = "saleor.plugins.telegram_notify"
    PLUGIN_NAME = "Telegram Bot"
    PLUGIN_DESCRIPTION = "Уведомляет подписанных администраторов " \
                         "о новых, измененных, отмененных и выполненный заказов."
    DEFAULT_ACTIVE = True
    DEFAULT_CONFIGURATION = [
        {"name": ConfNames.admin_telegram_usernames, "value": ''},
        {"name": ConfNames.notify_order_created, "value": True},
        {"name": ConfNames.notify_order_fulfilled, "value": True},
        {"name": ConfNames.notify_order_canceled, "value": True},
        {"name": ConfNames.notify_order_fully_paid, "value": True}
    ]
    CONFIG_STRUCTURE = {
        ConfNames.admin_telegram_usernames: {
            "type": ConfigurationTypeField.STRING,
            "help_text": "Введите имена пользователей разделив с запятыми. "
                         "Добавленные сотрудники должны будут написать боту /start.",
            "label": "Имена пользователей сотрудников в телеграм.",
        },
        ConfNames.notify_order_created: {
            "type": ConfigurationTypeField.BOOLEAN,
            "label": "Уведомить при регистрации заказа",
        },
        ConfNames.notify_order_fulfilled: {
            "type": ConfigurationTypeField.BOOLEAN,
            "label": "Уведомить при успешном выполении заказа",
        },
        ConfNames.notify_order_canceled: {
            "type": ConfigurationTypeField.BOOLEAN,
            "label": "Уведомить при отмене заказа",
        },
        ConfNames.notify_order_fully_paid: {
            "type": ConfigurationTypeField.BOOLEAN,
            "label": "Уведомить при полной оплате заказа",
        },
    }

    def order_created(self, order: "Order", previous_value: Any):
        self.notify_if_allowed(notify_type=self.ConfNames.notify_order_created,
                               task=telegram_order_create_notify,
                               order_id=order.id)

    def order_cancelled(self, order: "Order", previous_value: Any) -> Any:
        self.notify_if_allowed(notify_type=self.ConfNames.notify_order_canceled,
                               task=telegram_order_canceled_notify,
                               order_id=order.id)

    def order_fulfilled(self, order: "Order", previous_value: Any) -> Any:
        self.notify_if_allowed(notify_type=self.ConfNames.notify_order_fulfilled,
                               task=telegram_order_fulfilled_notify,
                               order_id=order.id)

    def order_fully_paid(self, order: "Order", previous_value: Any) -> Any:
        self.notify_if_allowed(notify_type=self.ConfNames.notify_order_fully_paid,
                               task=telegram_order_fully_paid_notify,
                               order_id=order.id)

    def notify_if_allowed(self, notify_type: str, task, **kwargs):
        if self.get_conf_item_value(notify_type):
            task.delay(**kwargs)

    @classmethod
    def get_allowed_usernames(cls):
        return cls.get_conf_item_value(
            item_name='admin_telegram_usernames').split(',')

    @classmethod
    def get_conf_item_value(cls, item_name: str):
        plugin_conf = cls.get_plugin_conf()

        username_conf_field = list(filter(
            lambda x: x['name'] == item_name,
            plugin_conf))

        if not username_conf_field:
            raise TypeError(
                f"Item \"{item_name}\" not found in "
                f"{cls.__name__} configuration")

        return username_conf_field[0]['value']

    @classmethod
    def get_plugin_conf(cls) -> list:
        try:
            return PluginConfiguration.objects.get(
                identifier=cls.PLUGIN_ID
            ).configuration
        except PluginConfiguration.DoesNotExist:
            return cls.DEFAULT_CONFIGURATION

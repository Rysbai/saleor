from typing import List

from saleor.plugins.models import PluginConfiguration
from saleor.telegram_notify import plugin


def get_allowed_usernames() -> List:
    return get_telegram_plugin_conf_item_value(
        item_name='admin_telegram_usernames').split(',')


def get_telegram_plugin_conf_item_value(item_name: str):
    plugin_conf = get_telegram_plugin_conf()

    username_conf_field = list(filter(
        lambda x : x['name'] == item_name,
        plugin_conf))

    if not username_conf_field:
        raise TypeError(
            f"Item \"{item_name}\" not found in "
            f"{plugin.TelegramOrderNotifyPlugin.__name__} configuration")

    return username_conf_field[0]['value']


def get_telegram_plugin_conf() -> list:
    try:
        return PluginConfiguration.objects.get(
            identifier=plugin.TelegramOrderNotifyPlugin.PLUGIN_ID
        ).configuration
    except PluginConfiguration.DoesNotExist:
        return plugin.TelegramOrderNotifyPlugin.DEFAULT_CONFIGURATION

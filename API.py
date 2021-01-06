import datetime

from NetworkWorker import network_worker


def send_message(bot, **kwargs):
    return network_worker(bot.send_message, False, **kwargs)


def restrict_chat_member(bot, pass_exception=False, **kwargs):
    return network_worker(bot.restrict_chat_member, pass_exception, **kwargs)


def delete_message(bot, chat_id, message_id, **kwargs):
    return network_worker(bot.delete_message, False, chat_id=chat_id, message_id=message_id, **kwargs)


def get_chat_member(bot, chat_id, user_id):
    return network_worker(bot.get_chat_member, False, chat_id=chat_id, user_id=user_id)


def kick_chat_member(bot, chat_id, user_id, until_date):
    return network_worker(bot.kick_chat_member, False, chat_id=chat_id, user_id=user_id, until_date=until_date)


def use_custom_api_method(func, **kwargs):
    return network_worker(func, False, **kwargs)

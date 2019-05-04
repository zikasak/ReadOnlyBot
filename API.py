from NetworkWorker import network_worker


def send_message(bot, **kwargs):
    return network_worker(bot.send_message, False, **kwargs)


def restrict_chat_member(bot, **kwargs):
    return network_worker(bot.restrict_chat_member, False, **kwargs)


def delete_message(bot, **kwargs):
    return network_worker(bot.delete_message, False, **kwargs)


def get_chat_member(bot, chat_id, user_id):
    return network_worker(bot.get_chat_member, False, chat_id=chat_id, user_id=user_id)


def use_custom_api_method(func, **kwargs):
    return network_worker(func, False, **kwargs)


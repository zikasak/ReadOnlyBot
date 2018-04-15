from NetworkWorker import network_worker


def is_user_admin(bot, update):
    chat_id = update.message.chat_id
    user_id = update.message.from_user.id
    us = network_worker(bot.get_chat_member, chat_id=chat_id, user_id=user_id)
    return us is not None and us.status in [us.CREATOR, us.ADMINISTRATOR]


def can_delete_messages(bot, update):
    chat_id = update.message.chat_id
    user_id = bot.id
    us = network_worker(bot.get_chat_member, chat_id=chat_id, user_id=user_id)
    return us.can_delete_messages

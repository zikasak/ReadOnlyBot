from NetworkWorker import network_worker


def is_user_admin(bot, update, user=None):
    chat_id = update.message.chat_id
    if user is None:
        user_id = update.message.from_user.id
    else:
        user_id = user.id
    us = network_worker(bot.get_chat_member, chat_id=chat_id, user_id=user_id)
    return us is not None and us.status in [us.CREATOR, us.ADMINISTRATOR]


def can_delete_messages(bot, update=None, chat_id = None):
    chat_id = update.message.chat_id if chat_id is None else chat_id
    user_id = bot.id
    us = network_worker(bot.get_chat_member, chat_id=chat_id, user_id=user_id)
    return us.can_delete_messages


def can_restrict_users(bot, update=None, chat_id=None):
    chat_id = update.message.chat_id if chat_id is None else chat_id
    user_id = bot.id
    us = network_worker(bot.get_chat_member, chat_id=chat_id, user_id=user_id)
    return us.can_restrict_members


def build_menu(buttons,
               n_cols,
               header_buttons=None,
               footer_buttons=None):
    menu = [buttons[i:i + n_cols] for i in range(0, len(buttons), n_cols)]
    if header_buttons:
        menu.insert(0, header_buttons)
    if footer_buttons:
        menu.append(footer_buttons)
    return menu



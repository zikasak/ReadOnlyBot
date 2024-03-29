import API
from logs import logger
from telegram import constants


def is_user_admin(bot, update, user=None):
    chat_id = update.message.chat_id
    if user is None:
        user_id = update.message.from_user.id
    else:
        user_id = user.id
    us = API.get_chat_member(bot, chat_id=chat_id, user_id=user_id)
    is_admin = (us is not None) and (us.status in [us.CREATOR, us.ADMINISTRATOR] or us.user.id
                                     == constants.ANONYMOUS_ADMIN_ID)
    logger.info(f"user: {us.user.username} {user_id} chat_id: {chat_id} is_admin: {is_admin}")
    return is_admin


def can_delete_messages(bot, update=None, chat_id=None):
    chat_id = update.message.chat_id if chat_id is None else chat_id
    user_id = bot.id
    us = API.get_chat_member(bot, chat_id=chat_id, user_id=user_id)
    right_to_delete = us.can_delete_messages
    logger.info(f"user: {us.user.username} {user_id} chat_id: {chat_id} can_delete_messages: {right_to_delete}")
    return right_to_delete


def can_restrict_users(bot, update=None, chat_id=None):
    chat_id = update.message.chat_id if chat_id is None else chat_id
    user_id = bot.id
    us = API.get_chat_member(bot, chat_id=chat_id, user_id=user_id)
    right_to_restrict = us.can_restrict_members
    logger.info(f"user: {us.user.username} {user_id} chat_id: {chat_id} can_restrict_users: {right_to_restrict}")
    return right_to_restrict


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

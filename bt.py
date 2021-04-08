import datetime

import telegram
from telegram import InlineKeyboardMarkup
from telegram.ext import Updater, CommandHandler, Filters, MessageHandler, CallbackQueryHandler
import API
from BtStatic import can_delete_messages, is_user_admin, can_restrict_users, build_menu
from Commands.CommandFactory import CommandFactory
from Commands.CommandsImpl import Command
from btConfig import TOKEN
from dbConfig import engine
from dbSchema import GroupStatus, MutedUser, BlockedPhrases
import dbWorker
import time
from logs import logger

dataWorker = dbWorker.DbWorker(engine)


def __set_read_only(update, context, status, message):
    bot = context.bot
    if not is_user_admin(bot, update):
        return
    if can_delete_messages(bot, update):
        API.delete_message(bot,
                           chat_id=update.message.chat_id,
                           message_id=update.message.message_id)
    change_read_only(update.message.chat_id, status)
    cmd, txt = Command.parse_command(update.message.text)
    API.send_message(bot, chat_id=update.message.chat_id, text=message)
    if txt is not None and txt != "":
        API.send_message(bot, chat_id=update.message.chat_id, text=txt)


def change_read_only(chat_id, status):
    with dataWorker.session_scope() as session:
        cur_status = session.query(GroupStatus).get(chat_id)
        if cur_status is None:
            gstatus = GroupStatus()
            gstatus.id = chat_id
            gstatus.status = status
            session.add(gstatus)
            return
        cur_status.status = status


def start_bot():
    updater.start_polling()
    updater.idle()


def is_need_delete(chat_id):
    with dataWorker.session_scope() as session:
        cur_status = session.query(GroupStatus).get(chat_id)
        delete_required = cur_status is not None and cur_status.status
        logger.info(f"chat_id: {chat_id} delete_required: {delete_required}")
        return delete_required


def __register_cmd_handler(cmd, command):
    dispatcher.add_handler(CommandHandler(cmd, command))


def __register_msg_handler(filter, command, **kwargs):
    dispatcher.add_handler(MessageHandler(filter, command, kwargs))


def start_read_only(bot, update):
    __set_read_only(bot, update, True, "Активирован режим 'Только чтение'. До момента отключения "
                                       "режима все сообщения будут удалены")


def end_read_only(bot, update):
    __set_read_only(bot, update, False, "Режим 'Только чтение' отключен")


def unlock_member(update, callback):
    """

            :param update: telegram.Update
            :type bot: telegram.Bot
    """
    chat_id = update.effective_chat.id
    bot = callback.bot
    if not can_restrict_users(bot, chat_id=chat_id):
        return
    query = update.callback_query
    if "applied" not in query.data:
        return
    user_id = update.effective_user.id
    if str(user_id) not in query.data:
        return
    with dataWorker.session_scope() as session:
        lock_info_query = session.query(MutedUser).filter(MutedUser.chat_id == chat_id,
                                                          MutedUser.user_id == user_id)
        lock_info: MutedUser = lock_info_query.first()
        current = datetime.datetime.utcnow()
        required = lock_info.mute_date
        time_to_mute = lock_info.chat.time_to_mute
        time_to_mute = 30 if time_to_mute is None else time_to_mute
        resulted_time = current - datetime.timedelta(seconds=time_to_mute)
        time_over = required < resulted_time
        if not time_over:
            message = API.send_message(bot, chat_id=chat_id, text="А лукавить нехорошо. Пожалуйста, прочитайте");
            dbWorker.add_time_message(lock_info, message)
            return
        API.restrict_chat_member(bot,
                                 pass_exception=True,
                                 chat_id=chat_id,
                                 user_id=user_id,
                                 permissions=telegram.ChatPermissions(
                                     can_send_messages=True,
                                     can_send_media_messages=True,
                                     can_send_other_messages=True,
                                     can_add_web_page_previews=True)
                                 )
        delete_welcome_message(lock_info, bot)
        session.delete(lock_info)


def proceed_message(update, context):
    bot = context.bot
    if not proceed_non_text_message(update, context):
        return

    cmd, txt = Command.parse_command(update.message.text)
    logger.info(f"chat_id: {update.message.chat_id} user_id: {update.message.from_user.id} cmd: {cmd}")
    if cmd == "":
        delete_blocked_phrases(update, context)
        return
    command_to_exec = CommandFactory.get_command_handler(cmd, dataWorker)
    if command_to_exec.is_admin_rights_needed and not is_user_admin(bot, update):
        if can_delete_messages(bot, update):
            API.delete_message(bot,
                               chat_id=update.message.chat_id,
                               message_id=update.message.message_id)
    else:
        command_to_exec.execute(bot, update, txt)


def delete_blocked_phrases(update, context):
    chat_id = update.effective_chat.id
    bot = context.bot
    message_id = update.message.message_id

    if not can_delete_messages(bot, update) or is_user_admin(bot, update, update.message.from_user.id):
        return

    with dataWorker.session_scope() as session:
        phrases_query = session.query(BlockedPhrases).filter(BlockedPhrases.chat_id == chat_id)
        phrases = phrases_query.all()
        text = " " + update.message.text.lower() + " "
        for phrase in phrases:
            search_phrase = " " + phrase.blockedPhrase + " "
            if search_phrase in text:
                API.delete_message(bot, chat_id, message_id)
                return


def send_wel_message(bot, kwargs):
    return API.send_message(bot, parse_mode="HTML", **kwargs)


def proceed_new_members(update, callback):
    bot = callback.bot
    members = update.message.new_chat_members
    logger.info(members)
    if len(members) == 0:
        return
    chat_id = update.message.chat_id
    API.delete_message(bot, chat_id, update.message.message_id)
    with dataWorker.session_scope() as session:
        chat: GroupStatus = session.query(GroupStatus).get(chat_id)
        reply_template = chat.wel_message
        if chat is None or reply_template is None:
            return
        for member in members:
            reply = reply_template.replace("""{$name}""",
                                           f"""<a href="tg://user?id={member.id}">{member.first_name}</a>""")
            kwargs = {"chat_id": chat_id,
                      "text": reply,
                      "disable_web_page_preview": True}
            if not chat.new_users_blocked or not can_restrict_users(bot, update):
                message = send_wel_message(bot, kwargs)
                time.sleep(30)
                if can_delete_messages(bot, update):
                    API.delete_message(bot, chat_id=message.chat_id, message_id=message.message_id)
            else:

                unlock_button = telegram.InlineKeyboardButton("Я прочитал",
                                                              callback_data="applied " + str(member.id))
                reply_markup = InlineKeyboardMarkup(build_menu([unlock_button], n_cols=1))
                kwargs["reply_markup"] = reply_markup
                msg = send_wel_message(bot, kwargs)
                chat.add_muted(member.id, msg.message_id)
                bot.restrict_chat_member(chat_id, member.id, telegram.ChatPermissions())


def proceed_non_text_message(update, callback):
    bot = callback.bot
    proceed_new_members(update, callback)
    if is_need_delete(update.message.chat_id) and \
            not is_user_admin(bot, update) and \
            can_delete_messages(bot, update):
        API.delete_message(bot,
                           chat_id=update.message.chat_id,
                           message_id=update.message.message_id)
        return False
    return True


def kicking_users(context):
    bot = context.bot
    current = datetime.datetime.utcnow()
    destination_time = current - datetime.timedelta(minutes=5)
    with dataWorker.session_scope() as session:
        users = session.query(MutedUser).filter(MutedUser.mute_date < destination_time).all()
        for user in users:
            kick_user(user, bot, session)


def kick_user(user, bot, session):
    if not can_delete_messages(bot, None, user.chat_id) or \
            not can_restrict_users(bot, None, user.chat_id):
        return
    chat_member = API.get_chat_member(bot, user.chat_id, user.user_id)
    if chat_member.is_member:
        API.kick_chat_member(bot, user.chat_id, user.user_id,
                             until_date=datetime.datetime.utcnow() + datetime.timedelta(
                                 seconds=60))
    delete_welcome_message(user, bot)
    session.delete(user)


def delete_welcome_message(lock_info: MutedUser, bot: telegram.bot):
    chat_id = lock_info.chat_id
    if not can_delete_messages(bot, chat_id=chat_id):
        return
    for message in lock_info.time_messages:
        API.delete_message(bot,
                           chat_id=chat_id,
                           message_id=message.msg_id)
    mess_id = lock_info.welcome_msg_id
    API.delete_message(bot,
                       chat_id=chat_id,
                       message_id=mess_id)


needDelete = False
updater = Updater(token=TOKEN,
                  request_kwargs={"read_timeout": 6, "connect_timeout": 7})
dispatcher = updater.dispatcher
__register_cmd_handler("startRO", start_read_only)
__register_cmd_handler("stopRO", end_read_only)
__register_msg_handler(Filters.text |
                       Filters.command, proceed_message, run_async=True)
__register_msg_handler(Filters.all &
                       ~ Filters.text &
                       ~ Filters.command, proceed_non_text_message, run_async=True)
dispatcher.add_handler(CallbackQueryHandler(unlock_member, pass_user_data=False))
updater.job_queue.run_repeating(kicking_users, interval=60)

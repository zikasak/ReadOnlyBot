import telegram
from telegram import InlineKeyboardMarkup
from telegram.ext import Updater, CommandHandler, Filters, MessageHandler, run_async, CallbackQueryHandler

import API
from BtStatic import can_delete_messages, is_user_admin, can_restrict_users, build_menu
from Commands.CommandFactory import CommandFactory
from Commands.CommandsImpl import Command
from btConfig import TOKEN
from dbConfig import engine
from dbSchema import GroupStatus, MutedUser
from dbWorker import DbWorker
import time


class Bt:

    def __init__(self):
        self.dbWorker = DbWorker(engine)
        self.needDelete = False
        self.updater = Updater(token=TOKEN,
                               request_kwargs={'read_timeout': 6, 'connect_timeout': 7})
        self.dispatcher = self.updater.dispatcher
        self.__register_cmd_handler('startRO', self.start_read_only)
        self.__register_cmd_handler('stopRO', self.end_read_only)
        self.__register_msg_handler(Filters.text |
                                    Filters.command, self.proceed_message)
        self.__register_msg_handler(Filters.all &
                                    ~ Filters.text &
                                    ~ Filters.command, self.proceed_non_text_message)
        self.dispatcher.add_handler(CallbackQueryHandler(self.unlock_member, pass_user_data=False))

    def unlock_member(self, bot, update):
        """

                :param update: telegram.Update
                :type bot: telegram.Bot
        """
        chat_id = update.effective_chat.id

        if not can_restrict_users(bot, chat_id=chat_id):
            return
        query = update.callback_query
        if "applied" not in query.data:
            return
        user_id = update.effective_user.id
        if str(user_id) not in query.data:
            return
        with self.dbWorker.session_scope() as session:
            API.restrict_chat_member(bot,
                                     passException=True,
                                     chat_id=chat_id,
                                     user_id=user_id,
                                     can_send_messages=True,
                                     can_send_media_messages=True,
                                     can_send_other_messages=True,
                                     can_add_web_page_previews=True
                                     )
            session.query(MutedUser).filter(MutedUser.chat_id == chat_id,
                                            MutedUser.user_id == user_id).delete()
        if not can_delete_messages(bot, chat_id=chat_id):
            return
        mess_id = update.effective_message.message_id
        API.delete_message(bot,
                           chat_id=chat_id,
                           message_id=mess_id)

    def proceed_all_mes(self, bot, update):
        """

        :param update: telegram.Update
        :type bot: telegram.Bot
        """
        members = update.message.new_chat_members
        with self.dbWorker.session_scope() as session:
            chat: GroupStatus = session.query(GroupStatus).get(update.message.chat_id)
            if chat is None:
                return
            for member in members:
                repl = chat.wel_message
                if repl is None:
                    return
                repl = repl.replace("""{$name}""", member.first_name)
                kwargs = {"chat_id": update.message.chat_id,
                          "text": repl,
                          "disable_web_page_preview": True}
                if not chat.new_users_blocked or not can_restrict_users(bot, update):
                    message = self.__send_wel_message(bot, kwargs)
                    time.sleep(30)
                    if can_delete_messages(bot, update):
                        API.delete_message(bot, chat_id=message.chat_id, message_id=message.message_id)
                else:
                    chat.add_muted(member.id)
                    unlock_button = telegram.InlineKeyboardButton("Я прочитал",
                                                                  callback_data="applied " + str(member.id))
                    reply_markup = InlineKeyboardMarkup(build_menu([unlock_button], n_cols=1))
                    kwargs["reply_markup"] = reply_markup
                    self.__send_wel_message(bot, kwargs)
                    bot.restrict_chat_member(update.message.chat_id, member.id)

    def __send_wel_message(self, bot, kwargs):
        return API.send_message(bot, kwargs)
        # return network_worker(bot.send_message, **kwargs)

    def __register_cmd_handler(self, cmd, command):
        self.dispatcher.add_handler(CommandHandler(cmd, command))

    def __register_msg_handler(self, filter, command):
        self.dispatcher.add_handler(MessageHandler(filter, command))

    def start_read_only(self, bot, update):
        self.__set_read_only(bot, update, True, "Активирован режим 'Только чтение'. До момента отключения "
                                                "режима все сообщения будут удалены")

    def end_read_only(self, bot, update):
        self.__set_read_only(bot, update, False, "Режим 'Только чтение' отключен")

    def __set_read_only(self, bot, update, status, message):
        if is_user_admin(bot, update):
            if can_delete_messages(bot, update):
                API.delete_message(bot,
                                   chat_id=update.message.chat_id,
                                   message_id=update.message.message_id)
            self.__change_read_only(update.message.chat_id, status)
            cmd, txt = Command.parse_command(update.message.text)
            API.send_message(bot, chat_id=update.message.chat_id, text=message)
            if txt is not None and txt != '':
                API.send_message(bot, chat_id=update.message.chat_id, text=txt)

    def __change_read_only(self, chat_id, status):
        with self.dbWorker.session_scope() as session:
            cur_status = session.query(GroupStatus).get(chat_id)
            if cur_status is None:
                gstatus = GroupStatus()
                gstatus.id = chat_id
                gstatus.status = status
                session.add(gstatus)
                return
            cur_status.status = status

    @run_async
    def proceed_non_text_message(self, bot, update):
        self.proceed_all_mes(bot, update)
        if self.is_need_delete(update.message.chat_id) and \
                not is_user_admin(bot, update) and \
                can_delete_messages(bot, update):
            API.delete_message(bot,
                               chat_id=update.message.chat_id,
                               message_id=update.message.message_id)
            return False
        return True

    @run_async
    def proceed_message(self, bot, update):
        if not self.proceed_non_text_message(bot, update):
            return
        cmd, txt = Command.parse_command(update.message.text)
        if cmd == '':
            return
        command_to_exec = CommandFactory.get_command_handler(cmd, self.dbWorker)
        if command_to_exec.is_admin_rights_needed and not is_user_admin(bot, update):
            if can_delete_messages(bot, update):
                API.delete_message(bot,
                                   chat_id=update.message.chat_id,
                                   message_id=update.message.message_id)
        else:
            command_to_exec.execute(bot, update, txt)

    def start_bot(self):
        self.updater.start_polling()

    def is_need_delete(self, chat_id):
        with self.dbWorker.session_scope() as session:
            cur_status = session.query(GroupStatus).get(chat_id)
            return cur_status is not None and cur_status.status

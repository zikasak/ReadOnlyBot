from telegram.ext import Updater, CommandHandler, Filters, MessageHandler, run_async

from BtStatic import can_delete_messages, is_user_admin
from Commands.CommandFactory import CommandFactory
from Commands.CommandsImpl import Command
from NetworkWorker import network_worker
from btConfig import TOKEN
from dbConfig import engine
from dbSchema import GroupStatus
from dbWorker import DbWorker


class Bt:

    def __init__(self):
        self.dbWorker = DbWorker(engine)
        self.needDelete = False
        self.updater = Updater(token= TOKEN,
                               request_kwargs={'read_timeout': 6, 'connect_timeout': 7})
        self.dispatcher = self.updater.dispatcher
        self.__register_cmd_handler('startRO', self.start_read_only)
        self.__register_cmd_handler('stopRO', self.end_read_only)
        self.__register_msg_handler(Filters.text |
                                    Filters.command, self.proceed_message)
        self.__register_msg_handler(Filters.all &
                                    ~ Filters.text &
                                    ~ Filters.command, self.proceed_non_text_message)

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
            self.__change_read_only(update.message.chat_id, status)
            network_worker(bot.send_message, chat_id=update.message.chat_id, text=message)

    def __change_read_only(self, chat_id, status):
        with self.dbWorker.session_scope() as session:
            cur_status = session.query(GroupStatus).get(chat_id)
            if cur_status is None:
                gstatus = GroupStatus()
                gstatus.id = chat_id
                gstatus.status = status
                session.add(gstatus)
                return
            cur = cur_status.status
            cur_status.status = status

    @run_async
    def proceed_non_text_message(self, bot, update):
        if self.is_need_delete(update.message.chat_id) and \
                not is_user_admin(bot, update) and \
                can_delete_messages(bot, update):
            network_worker(bot.delete_message,
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
                network_worker(bot.delete_message,
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

import re
from abc import abstractmethod, ABC

import API
from BtStatic import can_delete_messages, is_user_admin
from NetworkWorker import network_worker
from dbSchema import GroupMessage, GroupStatus, BannedUser


class Command:

    def __init__(self, db_worker, cmd, need_admin):
        self.dbWorker = db_worker
        self.cmd = cmd
        self.is_admin_rights_needed = need_admin

    @abstractmethod
    def execute(self, bot, update, txt):
        pass

    @staticmethod
    def parse_command(text: str):
        regexp = re.compile('(/\w+)( [\s\S\w]+)?').search(text)
        if regexp is None:
            return '', ''
        ind = text.index(regexp[0])
        if ind != 0:
            try:
                text.index(' ' + regexp[0])
            except ValueError:
                return '', ''

        return regexp.groups()


class AddCommand(Command):

    def __init__(self, db_worker, cmd):
        super().__init__(db_worker, cmd, True)

    def parse_command(self, text):
        regexp = re.compile('(/\w+)( (?:[\s\W\S]+)+)').search(text)
        if regexp is None:
            return '', ''
        return regexp.groups()

    def execute(self, bot, update, txt):
        with self.dbWorker.session_scope() as session:
            msg = GroupMessage()
            elem = self.parse_command(txt)
            msg.command = elem[0]
            msg.message = elem[1]
            mdl = session.query(GroupStatus).get(update.message.chat_id)
            if mdl is None:
                mdl = GroupStatus()
                mdl.status = False
                mdl.id = update.message.chat_id
                session.add(mdl)
            mdl.messages.append(msg)
        if can_delete_messages(bot, update):
            API.delete_message(bot,
                               chat_id=update.message.chat_id,
                               message_id=update.message.message_id)


class UpdateCommand(Command):

    def __init__(self, db_worker, cmd):
        super().__init__(db_worker, cmd, True)

    def execute(self, bot, update, txt):
        with self.dbWorker.session_scope() as session:
            elem = self.parse_command(txt)
            status = session.query(GroupStatus).get(update.message.chat_id)
            for i in status.messages:
                if i.command == elem[0]:
                    i.message = elem[1]
        if can_delete_messages(bot, update):
            API.delete_message(bot,
                               chat_id=update.message.chat_id,
                               message_id=update.message.message_id)


class DeleteCommand(Command):

    def __init__(self, db_worker, cmd):
        super().__init__(db_worker, cmd, True)

    def execute(self, bot, update, txt):
        with self.dbWorker.session_scope() as session:
            del_cmd = self.parse_command(txt)[0]
            mdl = session.query(GroupStatus).get(update.message.chat_id)
            # mdl = self.dbWorker.get_model(session, GroupStatus, update.message.chat_id)
            if mdl is not None:
                mdl.messages = list(filter(lambda x: x.command != del_cmd, mdl.messages))
        if can_delete_messages(bot, update):
            API.delete_message(bot,
                               chat_id=update.message.chat_id,
                               message_id=update.message.message_id)


class GetCommandsCommand(Command):

    def __init__(self, db_worker, cmd):
        super().__init__(db_worker, cmd, False)

    def execute(self, bot, update, txt):
        with self.dbWorker.session_scope() as session:
            group_messages = self.__get_group_messages(bot, update, session)
            group_messages = list(map(lambda x: str(x), group_messages))
        res_string = "Команды для чата {!r}: \n".format(update.message.chat.title)
        append_str = "\n".join(group_messages)
        API.send_message(bot, chat_id=update.message.from_user.id,
                         text=res_string + append_str)
        if can_delete_messages(bot, update):
            API.delete_message(bot,
                               chat_id=update.message.chat_id,
                               message_id=update.message.message_id)

    def __get_group_messages(self, bot, update, session):
        group_status = session.query(GroupStatus).get(update.message.chat_id)
        if group_status is None:
            return []
        else:
            return group_status.messages


class DefaultCommand(Command):

    def __init__(self, db_worker, cmd):
        super().__init__(db_worker, cmd, False)

    def execute(self, bot, update, txt):
        with self.dbWorker.session_scope() as session:
            mdl = session.query(GroupStatus).get(update.message.chat_id)
            if mdl is None:
                return
            cm = list(filter(lambda x: x.command == self.cmd, mdl.messages))
            if len(cm) == 0 or cm[0].message is None:
                return
            if update.message.reply_to_message is not None \
                    and not is_user_admin(bot, update, update.message.reply_to_message.from_user):
                reply_msg_id = update.message.reply_to_message.message_id
            else:
                reply_msg_id = None
            API.send_message(bot,
                             chat_id=update.message.chat_id,
                             reply_to_message_id=reply_msg_id,
                             text=cm[0].message)
            if can_delete_messages(bot, update):
                API.delete_message(bot,
                                   chat_id=update.message.chat_id,
                                   message_id=update.message.message_id)


class SetWelcomeMessage(Command):

    def __init__(self, db_worker, cmd):
        super().__init__(db_worker, cmd, True)

    def execute(self, bot, update, txt):
        pattern = re.compile('^(?P<param>b )?(?P<text>[\s\S\w]+)')
        m = pattern.search(txt.strip())
        text = m.group('text')
        isBlocking = m.group('param')
        isBlocking = isBlocking is not None and "" != isBlocking
        with self.dbWorker.session_scope() as session:
            group = session.query(GroupStatus).get(update.message.chat_id)
            if group is None:
                group = GroupStatus()
                group.id = update.message.chat_id
                session.add(group)
            if txt is None or text == '':
                group.wel_message = None
            else:
                group.wel_message = text
            group.new_users_blocked = isBlocking
        if can_delete_messages(bot, update):
            API.delete_message(bot,
                               chat_id=update.message.chat_id,
                               message_id=update.message.message_id)


class BanMuteCommand(Command, ABC):

    def __init__(self, db_worker, cmd):
        super().__init__(db_worker, cmd, True)

    def _execute(self, bot, update, txt, method, **kwargs):
        with self.dbWorker.session_scope() as session:
            mdl: GroupStatus = session.query(GroupStatus).get(update.message.chat_id)
            if mdl is None:
                mdl = GroupStatus()
                mdl.id = update.message.chat_id
                session.add(mdl)
            if update.message.reply_to_message is not None \
                    and not is_user_admin(bot, update, update.message.reply_to_message.from_user):
                reply_user_id = update.message.reply_to_message.from_user.id
            else:
                reply_user_id = None
            banned_user = list(filter(lambda x: x.user_id == reply_user_id, mdl.banned_users))
            if len(banned_user) > 0:
                user = banned_user[0]
            else:
                user = BannedUser()
            user.user_id = reply_user_id
            user.reason = txt
            user.username = update.message.reply_to_message.from_user.username
            mdl.banned_users.append(user)
            API.use_custom_api_method(method,
                                      chat_id=update.message.chat_id,
                                      user_id=reply_user_id, **kwargs)
        if can_delete_messages(bot, update):
            API.delete_message(bot,
                               chat_id=update.message.chat_id,
                               message_id=update.message.message_id)


class BanUser(BanMuteCommand):

    def __init__(self, db_worker, cmd):
        super().__init__(db_worker, cmd)

    def execute(self, bot, update, txt):
        self._execute(bot, update, txt, bot.kick_chat_member)


class MuteUser(BanMuteCommand):

    def __abs__(self):
        def __init__(self, db_worker, cmd):
            super().__init__(db_worker, cmd)

    def execute(self, bot, update, txt):
        self._execute(bot, update, txt, bot.restrict_chat_member,
                      can_send_messages=False,
                      can_send_media_messages=False,
                      can_send_other_messages=False,
                      can_add_web_page_previews=False)

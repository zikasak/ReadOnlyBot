from contextlib import contextmanager

import telegram
from sqlalchemy.orm import sessionmaker

from dbSchema import MutedUser, TimeExceededMessage


class DbWorker:

    def __init__(self, engine):
        self.engine = engine
        self.session = self.__get_session()

    @contextmanager
    def session_scope(self):
        ses = self.session()
        try:
            yield ses
            ses.commit()
        except:
            ses.rollback()
            raise
        finally:
            ses.close()

    def __get_session(self):
        return sessionmaker(bind=self.engine)


def add_time_message(lock_info: MutedUser, message: telegram.Message):
    time_message = TimeExceededMessage()
    time_message.msg_id = message.message_id
    time_message.chat_id = lock_info.chat_id
    time_message.user_id = lock_info.user_id
    time_message.welcome_msg_id = lock_info.welcome_msg_id
    lock_info.time_messages.append(time_message)


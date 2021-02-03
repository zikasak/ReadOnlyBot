import datetime
from sqlalchemy import Column, Integer, Boolean, ForeignKey, String, DateTime, UniqueConstraint
from sqlalchemy.orm import relationship

import timeUtil
from dbConfig import Base, engine


class GroupStatus(Base):
    __tablename__ = "groupstatus"
    id = Column(Integer, primary_key=True)
    status = Column(Boolean, default=False)
    wel_message = Column(String)
    new_users_blocked = Column(Boolean, default=False)
    messages = relationship("GroupMessage", cascade="save-update, merge, delete, delete-orphan")
    banned_users = relationship("BannedUser", cascade="save-update, merge, delete, delete-orphan")
    mutted_users = relationship("MutedUser", cascade="save-update, merge, delete, delete-orphan")

    def add_muted(self, user_id, message_id):
        m = MutedUser()
        m.chat_id = self.id
        m.user_id = user_id
        m.welcome_msg_id = message_id
        # m.mute_date = timeUtil.convert_date_to_utc(datetime.datetime.now())
        m.mute_date = datetime.datetime.now()
        if m not in self.mutted_users:
            self.mutted_users.append(m)


class GroupMessage(Base):
    __tablename__ = "groupmessage"
    id = Column(Integer, primary_key=True)
    chat_id = Column(Integer, ForeignKey("groupstatus.id"))
    message = Column(String)
    command = Column(String)
    description = Column(String, default="")
    UniqueConstraint('chat_id', 'command')

    def __repr__(self):
        return "{!r} - {!r}".format(self.command, self.description)


class MutedUser(Base):
    __tablename__ = "muted"
    id = Column(Integer, primary_key=True)
    chat_id = Column(Integer, ForeignKey("groupstatus.id"))
    user_id = Column(Integer)
    mute_date = Column(DateTime(timezone=True), nullable=False, default=datetime.datetime.now())
    welcome_msg_id = Column(Integer, nullable=False)
    time_messages = relationship("TimeExceededMessage", cascade="save-update, merge, delete, delete-orphan")

    def get_mute_date(self):
        return timeUtil.convert_date_to_local(self.mute_date)

    def __eq__(self, obj: object) -> bool:
        if type(obj) != MutedUser:
            return super().__eq__(obj)
        return (self.chat_id == obj.chat_id) and (self.user_id == obj.user_id)


class TimeExceededMessage(Base):
    __tablename__ = "mutedMessages"
    id = Column(Integer, primary_key=True)
    chat_id = Column(Integer, ForeignKey("groupstatus.id"))
    user_id = Column(Integer)
    welcome_msg_id = Column(Integer, ForeignKey("muted.welcome_msg_id"))
    msg_id = Column(Integer, nullable=False)
    

class BannedUser(Base):
    __tablename__ = "bannedusers"
    id = Column(Integer, primary_key=True)
    chat_id = Column(Integer, ForeignKey("groupstatus.id"))
    user_id = Column(Integer)
    username = Column(String)
    reason = Column(String)


Base.metadata.create_all(engine)

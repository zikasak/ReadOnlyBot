import datetime
from sqlalchemy import Column, Integer, Boolean, ForeignKey, String, DateTime, UniqueConstraint, ForeignKeyConstraint
from sqlalchemy.orm import relationship

from dbConfig import Base, engine


class GroupStatus(Base):
    __tablename__ = "groupstatus"
    id = Column(Integer, primary_key=True)
    status = Column(Boolean, default=False)
    wel_message = Column(String)
    new_users_blocked = Column(Boolean, default=False)
    time_to_mute = Column(Integer, default=30)
    messages = relationship("GroupMessage", cascade="save-update, merge, delete, delete-orphan")
    banned_users = relationship("BannedUser", cascade="save-update, merge, delete, delete-orphan")
    mutted_users = relationship("MutedUser", backref="chat", cascade="save-update, merge, delete, delete-orphan")
    blocked_phrases = relationship("BlockedPhrases", backref="chat", cascade="save-update, merge, delete, delete-orphan")

    def add_muted(self, user_id, message_id):
        m = MutedUser()
        m.chat_id = self.id
        m.user_id = user_id
        m.welcome_msg_id = message_id
        m.mute_date = datetime.datetime.utcnow()
        if m not in self.mutted_users:
            self.mutted_users.append(m)


class GroupMessage(Base):
    __tablename__ = "groupmessage"
    chat_id = Column(Integer, ForeignKey("groupstatus.id"), primary_key=True)
    message = Column(String)
    command = Column(String, primary_key=True)
    description = Column(String, default="")
    UniqueConstraint('chat_id', 'command')

    def __repr__(self):
        return "{!r} - {!r}".format(self.command, self.description)


class MutedUser(Base):
    __tablename__ = "muted"
    chat_id = Column(Integer, ForeignKey("groupstatus.id"), primary_key=True)
    user_id = Column(Integer, primary_key=True)
    mute_date = Column(DateTime(timezone=True), nullable=False, default=datetime.datetime.utcnow())
    welcome_msg_id = Column(Integer, nullable=False)
    time_messages = relationship("TimeExceededMessage", cascade="save-update, merge, delete, delete-orphan",
                                 primaryjoin="and_(MutedUser.chat_id==TimeExceededMessage.chat_id, "
                                             "MutedUser.user_id==TimeExceededMessage.user_id)")

    def __eq__(self, obj: object) -> bool:
        if type(obj) != MutedUser:
            return super().__eq__(obj)
        return (self.chat_id == obj.chat_id) and (self.user_id == obj.user_id)


class TimeExceededMessage(Base):
    __tablename__ = "mutedMessages"
    id = Column(Integer, primary_key=True)
    chat_id = Column(Integer)
    user_id = Column(Integer)
    welcome_msg_id = Column(Integer, ForeignKey("muted.welcome_msg_id"))
    msg_id = Column(Integer, nullable=False)
    __table_args__ = (ForeignKeyConstraint([chat_id, user_id], [MutedUser.chat_id, MutedUser.user_id]), {})


class BannedUser(Base):
    __tablename__ = "bannedusers"
    chat_id = Column(Integer, ForeignKey("groupstatus.id"), primary_key=True)
    user_id = Column(Integer, primary_key=True)
    username = Column(String)
    reason = Column(String)


class BlockedPhrases(Base):
    __tablename__ = "blockedPhrases"
    id = Column(Integer, primary_key=True)
    chat_id = Column(Integer, ForeignKey("groupstatus.id"))
    blockedPhrase = Column(String, nullable=False)

Base.metadata.create_all(engine)

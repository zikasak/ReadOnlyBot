from sqlalchemy import Column, Integer, Boolean, ForeignKey, String
from sqlalchemy.orm import relationship

from dbConfig import Base, engine


class GroupStatus(Base):
    __tablename__ = 'groupstatus'
    id = Column(Integer, primary_key=True)
    status = Column(Boolean, default=False)
    wel_message = Column(String)
    new_users_blocked = Column(Boolean, default=False)
    messages = relationship("GroupMessage", cascade="save-update, merge, delete, delete-orphan")
    banned_users = relationship('BannedUser', cascade="save-update, merge, delete, delete-orphan")
    mutted_users = relationship('MutedUser', cascade="save-update, merge, delete, delete-orphan")

    def add_muted(self, user_id):
        m = MutedUser()
        m.chat_id = self.id
        m.user_id = user_id
        if m not in self.mutted_users:
            self.mutted_users.append(m)


class GroupMessage(Base):
    __tablename__ = 'groupmessage'
    chat_id = Column(Integer, ForeignKey("groupstatus.id"), primary_key=True)
    message = Column(String)
    command = Column(String, primary_key=True)
    description = Column(String, default='')

    def __repr__(self):
        return '{!r} - {!r}'.format(self.command, self.description)


class MutedUser(Base):
    __tablename__ = 'muted'
    chat_id = Column(Integer, ForeignKey("groupstatus.id"), primary_key=True)
    user_id = Column(Integer, primary_key=True)

    def __eq__(self, o: object) -> bool:
        if type(o) != MutedUser:
            return super().__eq__(o)
        return (self.chat_id == o.chat_id) and (self.user_id == o.user_id)


class BannedUser(Base):
    __tablename__ = 'bannedusers'
    chat_id = Column(Integer, ForeignKey("groupstatus.id"), primary_key=True)
    user_id = Column(Integer, primary_key=True)
    username = Column(String)
    reason = Column(String)


Base.metadata.create_all(engine)

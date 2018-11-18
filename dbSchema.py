from sqlalchemy import Column, Integer, Boolean, ForeignKey, String
from sqlalchemy.orm import relationship

from dbConfig import Base, engine


class GroupStatus(Base):
    __tablename__ = 'groupstatus'
    id = Column(Integer, primary_key=True)
    status = Column(Boolean, default=False)
    wel_message = Column(String)
    messages = relationship("GroupMessage", cascade="save-update, merge, delete, delete-orphan")
    banned_users = relationship('BannedUser', cascade="save-update, merge, delete, delete-orphan")


class GroupMessage(Base):
    __tablename__ = 'groupmessage'
    chat_id = Column(Integer, ForeignKey("groupstatus.id"), primary_key=True)
    message = Column(String)
    command = Column(String, primary_key=True)
    description = Column(String, default='')

    def __repr__(self):
        return '{!r} - {!r}'.format(self.command, self.description)


class BannedUser(Base):
    __tablename__ = 'bannedusers'
    chat_id = Column(Integer, ForeignKey("groupstatus.id"), primary_key=True)
    user_id = Column(Integer, primary_key=True)
    username = Column(String)
    reason = Column(String)


Base.metadata.create_all(engine)

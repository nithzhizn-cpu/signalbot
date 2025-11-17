from sqlalchemy import Column, Integer, String, DateTime, ForeignKey
from sqlalchemy.orm import declarative_base
from datetime import datetime

Base = declarative_base()

class User(Base):
    tablename = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True)
    telegram_id = Column(String, nullable=True)
    token = Column(String, unique=True, index=True)
    pubkey = Column(String, nullable=True)

class Message(Base):
    tablename = "messages"

    id = Column(Integer, primary_key=True, index=True)
    from_id = Column(Integer, ForeignKey("users.id"))
    to_id = Column(Integer, ForeignKey("users.id"))
    iv = Column(String)
    ciphertext = Column(String)
    msg_type = Column(String, default="text")
    ttl_sec = Column(Integer, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

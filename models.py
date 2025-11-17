from sqlalchemy import Column, Integer, String, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime

from .database import Base


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True, nullable=False)
    telegram_id = Column(Integer, index=True, nullable=True)
    token = Column(String, unique=True, index=True, nullable=False)

    # Публічний E2EE ключ у вигляді JWK (JSON-рядок)
    pubkey = Column(String, nullable=True)


class Message(Base):
    __tablename__ = "messages"

    id = Column(Integer, primary_key=True, index=True)
    from_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    to_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    iv = Column(String, nullable=False)
    ciphertext = Column(String, nullable=False)
    msg_type = Column(String, default="text", nullable=False)
    ttl_sec = Column(Integer, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    from_user = relationship("User", foreign_keys=[from_id])
    to_user = relationship("User", foreign_keys=[to_id])

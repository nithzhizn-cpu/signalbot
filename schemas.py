from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime


class RegisterRequest(BaseModel):
    username: str
    telegram_id: Optional[int] = None


class UserOut(BaseModel):
    id: int
    username: str

    class Config:
        from_attributes = True


class MessageCreate(BaseModel):
    to: int
    iv: str
    ciphertext: str
    msg_type: str = "text"
    ttl_sec: Optional[int] = None


class MessageOut(BaseModel):
    id: int
    from_id: int
    to_id: int
    iv: str
    ciphertext: str
    msg_type: str
    ttl_sec: Optional[int]
    created_at: datetime

    class Config:
        from_attributes = True


class MessagesResponse(BaseModel):
    messages: List[MessageOut]


# E2EE pubkey
class PubKeyUpdate(BaseModel):
    pubkey: str   # JWK JSON як строка


class PubKeyOut(BaseModel):
    pubkey: str

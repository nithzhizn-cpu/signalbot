from pydantic import BaseModel
from typing import Optional, List

class RegisterRequest(BaseModel):
    username: str
    telegram_id: Optional[str] = None

class UserOut(BaseModel):
    id: int
    username: str

class PubKeyUpdate(BaseModel):
    pubkey: str

class PubKeyOut(BaseModel):
    pubkey: str

class MessageCreate(BaseModel):
    to: int
    iv: str
    ciphertext: str
    msg_type: Optional[str] = "text"
    ttl_sec: Optional[int] = None

class MessageOut(BaseModel):
    id: int
    from_id: int
    to_id: int
    iv: str
    ciphertext: str

class MessagesResponse(BaseModel):
    messages: List[MessageOut]

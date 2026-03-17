from typing import Optional, Dict, Any, List, Union
from datetime import datetime
from pydantic import BaseModel

class MessageBase(BaseModel):
    role: str
    content: str
    metadata: Optional[Dict[str, Any]] = None

class MessageCreate(MessageBase):
    conversation_id: int

class MessageUpdate(BaseModel):
    content: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None

class Message(MessageBase):
    id: Union[int, str]
    conversation_id: int
    timestamp: datetime

    class Config:
        from_attributes = True

class EmailMessage(MessageBase):
    id: str
    conversation_id: Optional[int] = None
    timestamp: datetime
    sender_email: str
    receiver_email: str
    thread_id: str
    subject: Optional[str] = None

    class Config:
        from_attributes = True

class WhatsappMessage(MessageBase):
    id: int
    conversation_id: int
    timestamp: datetime
    from_number: str
    group_id: Optional[str] = None
    attachments: Optional[List[str]] = None

    class Config:
        from_attributes = True
from typing import Optional
from datetime import datetime
from pydantic import BaseModel

class ConversationBase(BaseModel):
    agent: str
    title: Optional[str] = None

class ConversationCreate(ConversationBase):
    user_id: int

class ConversationUpdate(BaseModel):
    title: Optional[str] = None
    agent: Optional[str] = None

class Conversation(ConversationBase):
    id: int
    user_id: int
    created_at: datetime
    last_message_at: Optional[datetime] = None

    class Config:
        from_attributes = True

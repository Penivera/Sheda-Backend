from pydantic import BaseModel
from datetime import datetime
from typing import Optional


class ChatMessageSchema(BaseModel):
    sender_id: int
    receiver_id: int
    message: str
    timestamp: Optional[datetime] = None
    property_id: Optional[int] = None

    class Config:
        from_attributes = True

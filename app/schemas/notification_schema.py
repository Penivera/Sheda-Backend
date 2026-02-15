from typing import Any, Optional

from pydantic import BaseModel, Field

from app.utils.enums import TransactionEventEnum


class TransactionNotificationRequest(BaseModel):
    transaction_id: str = Field(..., description="Bid or transaction identifier")
    event: TransactionEventEnum
    recipient_user_id: int
    property_id: int
    metadata: Optional[dict[str, Any]] = None


class TransactionNotificationResponse(BaseModel):
    id: int
    transaction_id: str
    event: TransactionEventEnum
    recipient_user_id: int
    property_id: int
    metadata: Optional[dict[str, Any]] = None

    class Config:
        from_attributes = True

from datetime import datetime
from typing import Any, List, Optional

from pydantic import BaseModel

from app.utils.enums import TransactionActionEnum, TransactionStatusEnum


class TransactionPropertyInfo(BaseModel):
    id: Optional[int] = None
    blockchain_property_id: Optional[str] = None
    title: Optional[str] = None
    location: Optional[str] = None
    images: List[str] = []


class TransactionCounterpartyInfo(BaseModel):
    id: Optional[int] = None
    name: Optional[str] = None
    avatar_url: Optional[str] = None
    wallet_id: Optional[str] = None


class TransactionView(BaseModel):
    bid_id: str
    property_id: str
    status: TransactionStatusEnum
    action: Optional[TransactionActionEnum] = None
    bid_amount: Optional[str] = None
    stablecoin_token: Optional[str] = None
    document_token_id: Optional[str] = None
    escrow_release_tx: Optional[str] = None
    updated_at: Optional[datetime] = None
    property: Optional[TransactionPropertyInfo] = None
    counterparty: Optional[TransactionCounterpartyInfo] = None


class TransactionListResponse(BaseModel):
    data: List[TransactionView]


class TransactionUploadResponse(BaseModel):
    uploaded_urls: List[str]
    description: Optional[str] = None


class TimeoutCandidate(BaseModel):
    transaction_id: str
    property_id: str
    status: TransactionStatusEnum
    updated_at: Optional[datetime] = None


class TimeoutCandidatesResponse(BaseModel):
    data: List[TimeoutCandidate]

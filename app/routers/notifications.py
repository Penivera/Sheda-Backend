from fastapi import APIRouter, status

from app.schemas.notification_schema import (
    TransactionNotificationRequest,
    TransactionNotificationResponse,
)
from app.services.notifications import create_transaction_notification
from app.services.user_service import ActiveUser
from core.dependecies import DBSession


router = APIRouter(prefix="/notifications", tags=["Notifications"])


@router.post(
    "/transaction-update",
    response_model=TransactionNotificationResponse,
    status_code=status.HTTP_201_CREATED,
)
async def transaction_update(
    payload: TransactionNotificationRequest,
    current_user: ActiveUser,
    db: DBSession,
):
    notification = await create_transaction_notification(payload, db)
    return notification

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.transaction import TransactionNotification
from app.schemas.notification_schema import TransactionNotificationRequest
from app.services.transactions import upsert_transaction_from_event


async def create_transaction_notification(
    payload: TransactionNotificationRequest, db: AsyncSession
) -> TransactionNotification:
    notification = TransactionNotification(
        transaction_id=payload.transaction_id,
        event=payload.event,
        recipient_user_id=payload.recipient_user_id,
        property_id=payload.property_id,
        metadata_payload=payload.metadata,
    )
    db.add(notification)
    await db.commit()
    await db.refresh(notification)

    await upsert_transaction_from_event(
        transaction_id=payload.transaction_id,
        event=payload.event,
        property_id=payload.property_id,
        metadata=payload.metadata,
        db=db,
    )

    return notification

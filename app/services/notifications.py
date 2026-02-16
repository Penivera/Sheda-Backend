from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.transaction import DeviceToken, TransactionNotification
from app.schemas.notification_schema import (
    DeviceTokenRequest,
    TransactionNotificationRequest,
)
from app.services.transactions import upsert_transaction_from_event
from app.services.push import send_push_notification


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

    await send_push_notification(
        user_id=payload.recipient_user_id,
        title="Transaction update",
        body=f"Event: {payload.event}",
        data=payload.metadata or {},
        db=db,
    )

    return notification


async def register_device_token(
    payload: DeviceTokenRequest, user_id: int, db: AsyncSession
) -> DeviceToken:
    existing = await db.execute(
        select(DeviceToken).where(DeviceToken.device_token == payload.device_token)
    )
    token = existing.scalar_one_or_none()
    if token:
        if token.user_id != user_id:
            token.user_id = user_id
        token.platform = payload.platform
        db.add(token)
        await db.commit()
        await db.refresh(token)
        return token

    token = DeviceToken(
        user_id=user_id,
        device_token=payload.device_token,
        platform=payload.platform,
    )
    db.add(token)
    await db.commit()
    await db.refresh(token)
    return token


async def list_notifications(
    user_id: int,
    db: AsyncSession,
    unread_only: bool = False,
) -> list[TransactionNotification]:
    stmt = (
        select(TransactionNotification)
        .where(TransactionNotification.recipient_user_id == user_id)
        .order_by(TransactionNotification.created_at.desc())
    )
    if unread_only:
        stmt = stmt.where(TransactionNotification.is_read == False)
    result = await db.execute(stmt)
    return result.scalars().all()


async def mark_notification_read(
    notification_id: int, user_id: int, db: AsyncSession
) -> TransactionNotification | None:
    result = await db.execute(
        select(TransactionNotification).where(
            TransactionNotification.id == notification_id,
            TransactionNotification.recipient_user_id == user_id,
        )
    )
    notification = result.scalar_one_or_none()
    if not notification:
        return None

    notification.is_read = True
    db.add(notification)
    await db.commit()
    await db.refresh(notification)
    return notification

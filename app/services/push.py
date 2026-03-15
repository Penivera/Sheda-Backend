from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.transaction import DeviceToken
from core.logger import logger


async def send_push_notification(
    user_id: int,
    title: str,
    body: str,
    data: dict[str, Any] | None,
    db: AsyncSession,
) -> None:
    result = await db.execute(select(DeviceToken).where(DeviceToken.user_id == user_id))
    tokens = result.scalars().all()

    if not tokens:
        return

    for token in tokens:
        logger.info(
            "Push notification queued for user %s token %s: %s",
            user_id,
            token.device_token,
            title,
        )

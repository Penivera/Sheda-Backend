from sqlalchemy.future import select
from datetime import datetime, timezone
from apscheduler.schedulers.background import BackgroundScheduler
import asyncio
from core.configs import logger
from core.database import AsyncSessionLocal
from app.models.property import Contract, Property
from app.utils.enums import PropertyStatEnum


scheduler = BackgroundScheduler()


async def expire_contracts_task():
    """Task to check expired contracts and deactivate them"""
    async with AsyncSessionLocal() as db:
        now = datetime.now(timezone.utc)

        # Fetch expired contracts
        stmt = select(Contract).where(
            Contract.end_date <= now,
            Contract.is_active == True,  # Only active contracts
        )
        result = await db.execute(stmt)
        expired_contracts = result.scalars().all()

        for contract in expired_contracts:
            contract.is_active = False  # Deactivate contract

            # Reset property status
            stmt = select(Property).where(Property.id == contract.property_id)
            property_result = await db.execute(stmt)
            property = property_result.scalar_one_or_none()

            if property:
                property.status = PropertyStatEnum.available  # Mark as available again
        db.add(property)
        db.add(contract)
        await db.commit()
        await db.refresh(property)
        await db.refresh(contract)
        logger.info("Database updates applied")


# Schedule task to run daily
def start_scheduler():
    scheduler.add_job(
        func=lambda: asyncio.run(expire_contracts_task()),  # Run async function
        trigger="interval",
        hours=24,  # NOTE - Runs every 24 hours
    )
    scheduler.start()

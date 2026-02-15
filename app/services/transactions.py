from typing import Optional

from sqlalchemy import or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import aliased, selectinload

from app.models.property import Property
from app.models.transaction import TransactionAuditLog, TransactionRecord, WalletMapping
from app.models.user import BaseUser
from app.schemas.transaction_schema import (
    TransactionCounterpartyInfo,
    TransactionPropertyInfo,
    TransactionView,
)
from app.utils.enums import (
    TransactionActionEnum,
    TransactionEventEnum,
    TransactionStatusEnum,
)
from app.services.wallets import get_wallet_for_user


STATUS_FILTERS: dict[str, set[TransactionStatusEnum]] = {
    "ongoing": {
        TransactionStatusEnum.pending,
        TransactionStatusEnum.accepted,
        TransactionStatusEnum.docs_released,
        TransactionStatusEnum.docs_confirmed,
        TransactionStatusEnum.payment_released,
        TransactionStatusEnum.disputed,
    },
    "completed": {TransactionStatusEnum.completed},
    "cancelled": {TransactionStatusEnum.rejected, TransactionStatusEnum.cancelled},
}

EVENT_STATUS_MAP: dict[TransactionEventEnum, TransactionStatusEnum] = {
    TransactionEventEnum.bid_accepted: TransactionStatusEnum.accepted,
    TransactionEventEnum.bid_rejected: TransactionStatusEnum.rejected,
    TransactionEventEnum.docs_released: TransactionStatusEnum.docs_released,
    TransactionEventEnum.docs_confirmed: TransactionStatusEnum.docs_confirmed,
    TransactionEventEnum.payment_released: TransactionStatusEnum.payment_released,
}


async def get_transactions(
    status_filter: Optional[str],
    current_user: BaseUser,
    db: AsyncSession,
) -> list[TransactionView]:
    wallet_mapping = await get_wallet_for_user(current_user.id, db)
    if not wallet_mapping:
        return []

    wallet_id = wallet_mapping.wallet_id

    buyer_wallet = aliased(WalletMapping)
    seller_wallet = aliased(WalletMapping)
    buyer_user = aliased(BaseUser)
    seller_user = aliased(BaseUser)

    stmt = (
        select(TransactionRecord, Property, buyer_user, seller_user)
        .outerjoin(
            Property, Property.blockchain_property_id == TransactionRecord.property_id
        )
        .outerjoin(
            buyer_wallet, buyer_wallet.wallet_id == TransactionRecord.buyer_wallet_id
        )
        .outerjoin(
            seller_wallet, seller_wallet.wallet_id == TransactionRecord.seller_wallet_id
        )
        .outerjoin(buyer_user, buyer_user.id == buyer_wallet.user_id)
        .outerjoin(seller_user, seller_user.id == seller_wallet.user_id)
        .where(
            or_(
                TransactionRecord.buyer_wallet_id == wallet_id,
                TransactionRecord.seller_wallet_id == wallet_id,
            )
        )
        .options(selectinload(Property.images))
    )

    if status_filter:
        normalized = status_filter.strip().lower()
        statuses = STATUS_FILTERS.get(normalized, set())
        if statuses:
            stmt = stmt.where(TransactionRecord.status.in_(statuses))

    result = await db.execute(stmt)

    transactions: list[TransactionView] = []
    for record, property_obj, buyer, seller in result.all():
        is_buyer = record.buyer_wallet_id == wallet_id
        counterparty_user = seller if is_buyer else buyer
        counterparty_wallet = (
            record.seller_wallet_id if is_buyer else record.buyer_wallet_id
        )

        property_info = None
        if property_obj:
            property_info = TransactionPropertyInfo(
                id=property_obj.id,
                blockchain_property_id=property_obj.blockchain_property_id,
                title=property_obj.title,
                location=property_obj.location,
                images=[img.image_url for img in property_obj.images],
            )

        counterparty_info = None
        if counterparty_user or counterparty_wallet:
            counterparty_info = TransactionCounterpartyInfo(
                id=counterparty_user.id if counterparty_user else None,
                name=(
                    counterparty_user.fullname
                    if counterparty_user and counterparty_user.fullname
                    else (
                        counterparty_user.username
                        if counterparty_user
                        else counterparty_user.email if counterparty_user else None
                    )
                ),
                avatar_url=counterparty_user.avatar_url if counterparty_user else None,
                wallet_id=counterparty_wallet,
            )

        transactions.append(
            TransactionView(
                bid_id=record.bid_id,
                property_id=record.property_id,
                status=record.status,
                action=record.action,
                bid_amount=record.bid_amount,
                stablecoin_token=record.stablecoin_token,
                document_token_id=record.document_token_id,
                escrow_release_tx=record.escrow_release_tx,
                updated_at=record.updated_at,
                property=property_info,
                counterparty=counterparty_info,
            )
        )

    return transactions


def _parse_action(value: Optional[str]) -> TransactionActionEnum | None:
    if not value:
        return None
    try:
        return TransactionActionEnum(value)
    except ValueError:
        return None


async def upsert_transaction_from_event(
    transaction_id: str,
    event: TransactionEventEnum,
    property_id: int,
    metadata: Optional[dict],
    db: AsyncSession,
) -> TransactionRecord:
    status = EVENT_STATUS_MAP[event]
    result = await db.execute(
        select(TransactionRecord).where(TransactionRecord.bid_id == transaction_id)
    )
    record = result.scalar_one_or_none()

    if record:
        from_status = record.status.value
        record.status = status
    else:
        record = TransactionRecord(
            bid_id=transaction_id,
            property_id=str(property_id),
            status=status,
        )
        from_status = None

    if metadata:
        record.metadata_payload = metadata
        record.document_token_id = metadata.get(
            "document_token_id", record.document_token_id
        )
        record.escrow_release_tx = metadata.get(
            "escrow_release_tx", record.escrow_release_tx
        )
        record.bid_amount = (
            str(metadata.get("bid_amount"))
            if metadata.get("bid_amount")
            else record.bid_amount
        )
        record.stablecoin_token = metadata.get(
            "stablecoin_token", record.stablecoin_token
        )
        record.buyer_wallet_id = metadata.get("buyer_wallet_id", record.buyer_wallet_id)
        record.seller_wallet_id = metadata.get(
            "seller_wallet_id", record.seller_wallet_id
        )
        record.action = _parse_action(metadata.get("action")) or record.action

    db.add(record)
    await db.commit()
    await db.refresh(record)

    audit = TransactionAuditLog(
        bid_id=record.bid_id,
        property_id=record.property_id,
        from_status=from_status,
        to_status=record.status.value,
        actor_wallet_id=metadata.get("actor_wallet_id") if metadata else None,
        tx_hash=metadata.get("tx_hash") if metadata else None,
        metadata_payload=metadata,
    )
    db.add(audit)
    await db.commit()

    return record

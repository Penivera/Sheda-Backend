"""Transaction lifecycle tables

Revision ID: 9b3f7a1c2d0e
Revises: cb2214d6a21f
Create Date: 2026-02-15 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "9b3f7a1c2d0e"
down_revision: Union[str, Sequence[str], None] = "cb2214d6a21f"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    transaction_status = sa.Enum(
        "pending",
        "accepted",
        "rejected",
        "cancelled",
        "docs_released",
        "docs_confirmed",
        "payment_released",
        "completed",
        "disputed",
        name="transaction_status_enum",
    )
    transaction_event = sa.Enum(
        "bid_accepted",
        "bid_rejected",
        "docs_released",
        "docs_confirmed",
        "payment_released",
        name="transaction_event_enum",
    )
    transaction_action = sa.Enum(
        "purchase",
        "lease",
        name="transaction_action_enum",
    )

    op.create_table(
        "wallet_mapping",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("wallet_id", sa.String(length=255), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["user.id"], ondelete="CASCADE"),
        sa.UniqueConstraint("wallet_id"),
    )
    op.create_index("ix_wallet_mapping_wallet_id", "wallet_mapping", ["wallet_id"])

    op.create_table(
        "transaction_record",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("bid_id", sa.String(length=64), nullable=False),
        sa.Column("property_id", sa.String(length=64), nullable=False),
        sa.Column("status", transaction_status, nullable=False),
        sa.Column("action", transaction_action, nullable=True),
        sa.Column("bid_amount", sa.String(length=64), nullable=True),
        sa.Column("stablecoin_token", sa.String(length=255), nullable=True),
        sa.Column("buyer_wallet_id", sa.String(length=255), nullable=True),
        sa.Column("seller_wallet_id", sa.String(length=255), nullable=True),
        sa.Column("document_token_id", sa.String(length=255), nullable=True),
        sa.Column("escrow_release_tx", sa.String(length=255), nullable=True),
        sa.Column("metadata", sa.JSON(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_transaction_record_bid_id", "transaction_record", ["bid_id"])
    op.create_index(
        "ix_transaction_record_property_id", "transaction_record", ["property_id"]
    )

    op.create_table(
        "transaction_notification",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("transaction_id", sa.String(length=64), nullable=False),
        sa.Column("event", transaction_event, nullable=False),
        sa.Column("recipient_user_id", sa.Integer(), nullable=False),
        sa.Column("property_id", sa.Integer(), nullable=False),
        sa.Column("metadata", sa.JSON(), nullable=True),
        sa.Column("is_read", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["recipient_user_id"], ["user.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["property_id"], ["property.id"], ondelete="CASCADE"),
    )
    op.create_index(
        "ix_transaction_notification_transaction_id",
        "transaction_notification",
        ["transaction_id"],
    )

    op.create_table(
        "transaction_audit_log",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("bid_id", sa.String(length=64), nullable=False),
        sa.Column("property_id", sa.String(length=64), nullable=False),
        sa.Column("from_status", sa.String(length=64), nullable=True),
        sa.Column("to_status", sa.String(length=64), nullable=False),
        sa.Column("actor_wallet_id", sa.String(length=255), nullable=True),
        sa.Column("tx_hash", sa.String(length=255), nullable=True),
        sa.Column("metadata", sa.JSON(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index(
        "ix_transaction_audit_log_bid_id", "transaction_audit_log", ["bid_id"]
    )

    op.create_table(
        "minted_property_draft",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("blockchain_property_id", sa.String(length=64), nullable=False),
        sa.Column("owner_wallet_id", sa.String(length=255), nullable=False),
        sa.Column("metadata_uri", sa.String(length=255), nullable=True),
        sa.Column("title", sa.String(length=255), nullable=True),
        sa.Column("description", sa.String(), nullable=True),
        sa.Column("linked_property_id", sa.Integer(), nullable=True),
        sa.Column("linked_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["linked_property_id"], ["property.id"], ondelete="SET NULL"),
        sa.UniqueConstraint("blockchain_property_id"),
    )


def downgrade() -> None:
    op.drop_table("minted_property_draft")
    op.drop_index("ix_transaction_audit_log_bid_id", table_name="transaction_audit_log")
    op.drop_table("transaction_audit_log")
    op.drop_index(
        "ix_transaction_notification_transaction_id",
        table_name="transaction_notification",
    )
    op.drop_table("transaction_notification")
    op.drop_index("ix_transaction_record_property_id", table_name="transaction_record")
    op.drop_index("ix_transaction_record_bid_id", table_name="transaction_record")
    op.drop_table("transaction_record")
    op.drop_index("ix_wallet_mapping_wallet_id", table_name="wallet_mapping")
    op.drop_table("wallet_mapping")

    op.execute("DROP TYPE IF EXISTS transaction_action_enum")
    op.execute("DROP TYPE IF EXISTS transaction_event_enum")
    op.execute("DROP TYPE IF EXISTS transaction_status_enum")

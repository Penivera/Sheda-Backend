"""Device token registrations

Revision ID: 4f1b9e0c7d2a
Revises: 9b3f7a1c2d0e
Create Date: 2026-02-15 00:00:00.000000

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "4f1b9e0c7d2a"
down_revision: Union[str, Sequence[str], None] = "9b3f7a1c2d0e"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "device_token",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("device_token", sa.String(length=255), nullable=False),
        sa.Column("platform", sa.String(length=50), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["user.id"], ondelete="CASCADE"),
        sa.UniqueConstraint("device_token"),
    )
    op.create_index("ix_device_token_device_token", "device_token", ["device_token"])


def downgrade() -> None:
    op.drop_index("ix_device_token_device_token", table_name="device_token")
    op.drop_table("device_token")

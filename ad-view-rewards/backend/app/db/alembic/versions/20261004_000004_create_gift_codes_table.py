"""create gift_codes table

Revision ID: 20261004_000004
Revises: 20261003_000003
Create Date: 2026-10-04 00:00:04
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = "20261004_000004"
down_revision: Union[str, None] = "20261003_000003"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "gift_codes",
        sa.Column("id", sa.Uuid(as_uuid=True), nullable=False),
        sa.Column("code", sa.String(length=255), nullable=False),
        sa.Column("provider", sa.String(length=50), nullable=False),
        sa.Column("assigned_to_user_id", sa.Uuid(as_uuid=True), nullable=True),
        sa.Column("redeemed", sa.Boolean(), server_default=sa.text("false"), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["assigned_to_user_id"], ["users.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("code"),
    )
    op.create_index(op.f("ix_gift_codes_code"), "gift_codes", ["code"], unique=True)


def downgrade() -> None:
    op.drop_index(op.f("ix_gift_codes_code"), table_name="gift_codes")
    op.drop_table("gift_codes")

"""create ads table

Revision ID: 20261002_000002
Revises: 20261001_000001
Create Date: 2026-10-02 00:00:02
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = "20261002_000002"
down_revision: Union[str, None] = "20261001_000001"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "ads",
        sa.Column("id", sa.Uuid(as_uuid=True), nullable=False),
        sa.Column("advertiser_id", sa.Uuid(as_uuid=True), nullable=True),
        sa.Column("title", sa.String(length=255), nullable=False),
        sa.Column("video_url", sa.String(length=2048), nullable=False),
        sa.Column("reward_point", sa.Integer(), nullable=False),
        sa.Column("budget", sa.Integer(), nullable=False),
        sa.Column("remaining_budget", sa.Integer(), nullable=False),
        sa.Column("is_active", sa.Boolean(), server_default=sa.text("true"), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )


def downgrade() -> None:
    op.drop_table("ads")

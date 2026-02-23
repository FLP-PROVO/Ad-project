"""create ad_views and points_ledger tables

Revision ID: 20261003_000003
Revises: 20261002_000002
Create Date: 2026-10-03 00:00:03
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = "20261003_000003"
down_revision: Union[str, None] = "20261002_000002"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "ad_views",
        sa.Column("id", sa.Uuid(as_uuid=True), nullable=False),
        sa.Column("ad_id", sa.Uuid(as_uuid=True), nullable=False),
        sa.Column("viewer_id", sa.Uuid(as_uuid=True), nullable=False),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("completed", sa.Boolean(), server_default=sa.text("false"), nullable=False),
        sa.Column("reward_granted", sa.Boolean(), server_default=sa.text("false"), nullable=False),
        sa.Column("client_info", sa.JSON(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["ad_id"], ["ads.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["viewer_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("ad_id", "viewer_id", name="uq_ad_views_ad_id_viewer_id"),
    )

    op.create_table(
        "points_ledger",
        sa.Column("id", sa.Uuid(as_uuid=True), nullable=False),
        sa.Column("user_id", sa.Uuid(as_uuid=True), nullable=False),
        sa.Column("change", sa.Integer(), nullable=False),
        sa.Column("reason", sa.String(length=50), nullable=False),
        sa.Column("reference_id", sa.Uuid(as_uuid=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["reference_id"], ["ad_views.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("reference_id"),
    )


def downgrade() -> None:
    op.drop_table("points_ledger")
    op.drop_table("ad_views")

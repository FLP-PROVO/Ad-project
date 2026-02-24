"""add ad file metadata columns

Revision ID: 20261005_000005
Revises: 20261004_000004
Create Date: 2026-10-05 00:00:05
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = "20261005_000005"
down_revision: Union[str, None] = "20261004_000004"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("ads", sa.Column("file_path", sa.Text(), nullable=True))
    op.add_column("ads", sa.Column("duration_seconds", sa.Integer(), nullable=True))
    op.add_column("ads", sa.Column("file_size_bytes", sa.BigInteger(), nullable=True))
    op.add_column(
        "ads",
        sa.Column("status", sa.String(length=16), nullable=False, server_default="ready"),
    )


def downgrade() -> None:
    op.drop_column("ads", "status")
    op.drop_column("ads", "file_size_bytes")
    op.drop_column("ads", "duration_seconds")
    op.drop_column("ads", "file_path")

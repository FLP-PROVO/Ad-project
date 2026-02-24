"""refine ad_views tracking fields and add daily uniqueness index

Revision ID: 20261006_000006
Revises: 20261005_000005
Create Date: 2026-10-06 00:00:06
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = "20261006_000006"
down_revision: Union[str, None] = "20261005_000005"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    bind = op.get_bind()
    dialect = bind.dialect.name

    with op.batch_alter_table("ad_views") as batch_op:
        batch_op.drop_constraint("uq_ad_views_ad_id_viewer_id", type_="unique")
        batch_op.drop_column("completed")
        batch_op.drop_column("reward_granted")
        batch_op.add_column(sa.Column("watched_seconds", sa.Integer(), nullable=True))
        batch_op.add_column(sa.Column("completion_rate", sa.Numeric(5, 2), nullable=True))
        batch_op.add_column(
            sa.Column("rewarded", sa.Boolean(), nullable=False, server_default=sa.text("false"))
        )
        batch_op.add_column(
            sa.Column("rewarded_points", sa.Integer(), nullable=False, server_default=sa.text("0"))
        )
        batch_op.alter_column("client_info", existing_type=sa.JSON(), nullable=True)

    if dialect == "postgresql":
        op.execute("ALTER TABLE ad_views ALTER COLUMN client_info TYPE JSONB USING client_info::jsonb")
        op.execute(
            "CREATE UNIQUE INDEX ux_ad_view_user_ad_date "
            "ON ad_views(viewer_id, ad_id, (date_trunc('day', created_at)))"
        )
    else:
        op.execute(
            "CREATE UNIQUE INDEX ux_ad_view_user_ad_date "
            "ON ad_views(viewer_id, ad_id, date(created_at))"
        )


def downgrade() -> None:
    bind = op.get_bind()
    dialect = bind.dialect.name

    op.drop_index("ux_ad_view_user_ad_date", table_name="ad_views")

    if dialect == "postgresql":
        op.execute("ALTER TABLE ad_views ALTER COLUMN client_info TYPE JSON USING client_info::json")

    with op.batch_alter_table("ad_views") as batch_op:
        batch_op.alter_column("client_info", existing_type=sa.JSON(), nullable=False)
        batch_op.drop_column("rewarded_points")
        batch_op.drop_column("rewarded")
        batch_op.drop_column("completion_rate")
        batch_op.drop_column("watched_seconds")
        batch_op.add_column(
            sa.Column("reward_granted", sa.Boolean(), nullable=False, server_default=sa.text("false"))
        )
        batch_op.add_column(sa.Column("completed", sa.Boolean(), nullable=False, server_default=sa.text("false")))
        batch_op.create_unique_constraint("uq_ad_views_ad_id_viewer_id", ["ad_id", "viewer_id"])

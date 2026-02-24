import uuid
from datetime import datetime
from decimal import Decimal

import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


json_type = sa.JSON().with_variant(JSONB, "postgresql")


class AdView(Base):
    __tablename__ = "ad_views"
    __table_args__ = (
        sa.Index(
            "ux_ad_view_user_ad_date",
            "viewer_id",
            "ad_id",
            sa.text("date(created_at)"),
            unique=True,
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(sa.Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    ad_id: Mapped[uuid.UUID] = mapped_column(sa.Uuid(as_uuid=True), sa.ForeignKey("ads.id", ondelete="CASCADE"), nullable=False)
    viewer_id: Mapped[uuid.UUID] = mapped_column(
        sa.Uuid(as_uuid=True), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    started_at: Mapped[datetime] = mapped_column(sa.DateTime(timezone=True), nullable=False)
    completed_at: Mapped[datetime | None] = mapped_column(sa.DateTime(timezone=True), nullable=True)
    watched_seconds: Mapped[int | None] = mapped_column(sa.Integer(), nullable=True)
    completion_rate: Mapped[Decimal | None] = mapped_column(sa.Numeric(5, 2), nullable=True)
    rewarded: Mapped[bool] = mapped_column(sa.Boolean(), nullable=False, default=False, server_default=sa.text("false"))
    rewarded_points: Mapped[int] = mapped_column(sa.Integer(), nullable=False, default=0, server_default=sa.text("0"))
    client_info: Mapped[dict | None] = mapped_column(json_type, nullable=True)
    created_at: Mapped[datetime] = mapped_column(sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now())

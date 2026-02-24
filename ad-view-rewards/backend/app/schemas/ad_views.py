import uuid
from datetime import datetime, timezone
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field


class AdViewCreate(BaseModel):
    ad_id: uuid.UUID
    started_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    client_info: dict | None = None


class AdViewResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    ad_id: uuid.UUID
    viewer_id: uuid.UUID
    started_at: datetime
    completed_at: datetime | None
    watched_seconds: int | None
    completion_rate: Decimal | None
    rewarded: bool
    rewarded_points: int
    client_info: dict | None
    created_at: datetime

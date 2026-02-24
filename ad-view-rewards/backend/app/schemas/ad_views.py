import uuid
from datetime import datetime, timezone
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field


class AdViewCreate(BaseModel):
    ad_id: uuid.UUID
    started_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    client_info: dict | None = None


class AdViewStartResponse(BaseModel):
    view_id: uuid.UUID
    started_at: datetime


class AdViewCompleteRequest(BaseModel):
    view_id: uuid.UUID
    watched_seconds: int = Field(ge=0)


class AdViewCompleteResponse(BaseModel):
    status: str
    rewarded_points: int
    new_balance: int


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

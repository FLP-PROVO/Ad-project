import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict


class AdViewRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    ad_id: uuid.UUID
    viewer_id: uuid.UUID
    started_at: datetime
    completed_at: datetime | None
    completed: bool
    reward_granted: bool
    created_at: datetime

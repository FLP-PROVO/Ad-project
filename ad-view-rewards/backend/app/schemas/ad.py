import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, field_validator, model_validator


class AdCreate(BaseModel):
    advertiser_id: uuid.UUID | None = None
    title: str
    video_url: str
    reward_point: int
    budget: int
    is_active: bool = True

    @field_validator("reward_point")
    @classmethod
    def validate_reward_point(cls, value: int) -> int:
        if value <= 0:
            raise ValueError("reward_point must be greater than 0")
        return value

    @model_validator(mode="after")
    def validate_budget(self) -> "AdCreate":
        if self.budget < self.reward_point:
            raise ValueError("budget must be greater than or equal to reward_point")
        return self


class AdRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    advertiser_id: uuid.UUID | None
    title: str
    video_url: str
    reward_point: int
    budget: int
    remaining_budget: int
    is_active: bool
    created_at: datetime

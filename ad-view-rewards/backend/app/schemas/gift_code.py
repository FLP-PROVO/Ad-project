import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class GiftCodeUploadJson(BaseModel):
    provider: str = Field(min_length=2, max_length=50)
    codes: list[str] = Field(min_length=1)


class GiftCodeRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    code: str
    provider: str
    assigned_to_user_id: uuid.UUID | None
    redeemed: bool
    created_at: datetime


class GiftCodeRedeemRequest(BaseModel):
    code: str = Field(min_length=1, max_length=255)
    user_id: uuid.UUID

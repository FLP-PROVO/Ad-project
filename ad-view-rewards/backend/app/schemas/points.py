import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict


class BalanceRead(BaseModel):
    balance: int


class LedgerEntryRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    user_id: uuid.UUID
    change: int
    reason: str
    reference_id: uuid.UUID
    created_at: datetime


class LedgerPageRead(BaseModel):
    page: int
    limit: int
    total: int
    items: list[LedgerEntryRead]

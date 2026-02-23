from fastapi import APIRouter, Depends, Query
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.core.security import get_current_user
from app.db.base import get_db
from app.models.points_ledger import PointsLedger
from app.models.user import User
from app.schemas.points import BalanceRead, LedgerEntryRead, LedgerPageRead
from app.schemas.user import UserRead

router = APIRouter()


@router.get('/me', response_model=UserRead)
def read_me(current_user: User = Depends(get_current_user)) -> UserRead:
    return UserRead.model_validate(current_user)


@router.get('/me/balance', response_model=BalanceRead)
def read_my_balance(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> BalanceRead:
    balance = (
        db.query(func.coalesce(func.sum(PointsLedger.change), 0))
        .filter(PointsLedger.user_id == current_user.id)
        .scalar()
    )
    return BalanceRead(balance=int(balance or 0))


@router.get('/me/ledger', response_model=LedgerPageRead)
def read_my_ledger(
    page: int = Query(default=1, ge=1),
    limit: int = Query(default=20, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> LedgerPageRead:
    query = db.query(PointsLedger).filter(PointsLedger.user_id == current_user.id)
    total = query.count()

    entries = (
        query.order_by(PointsLedger.created_at.desc())
        .offset((page - 1) * limit)
        .limit(limit)
        .all()
    )

    return LedgerPageRead(
        page=page,
        limit=limit,
        total=total,
        items=[LedgerEntryRead.model_validate(entry) for entry in entries],
    )

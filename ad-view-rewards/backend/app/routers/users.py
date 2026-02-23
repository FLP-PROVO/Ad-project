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


@router.get(
    '/me',
    response_model=UserRead,
    responses={
        200: {
            "description": "Current user profile",
            "content": {
                "application/json": {
                    "examples": {
                        "viewer_profile": {
                            "value": {
                                "id": "17cf3f5f-03bb-492a-bbc4-34a6ad4a4353",
                                "email": "viewer@example.com",
                                "role": "viewer",
                                "phone_number": "+81-90-1234-5678",
                                "created_at": "2026-10-01T12:00:00Z",
                            }
                        }
                    }
                }
            },
        }
    },
)
def read_me(current_user: User = Depends(get_current_user)) -> UserRead:
    return UserRead.model_validate(current_user)


@router.get(
    '/me/balance',
    response_model=BalanceRead,
    responses={
        200: {
            "description": "Current user points balance",
            "content": {
                "application/json": {
                    "examples": {
                        "balance": {
                            "value": {
                                "balance": 120,
                            }
                        }
                    }
                }
            },
        }
    },
)
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


@router.get(
    '/me/ledger',
    response_model=LedgerPageRead,
    responses={
        200: {
            "description": "Current user points ledger",
            "content": {
                "application/json": {
                    "examples": {
                        "ledger_page": {
                            "value": {
                                "page": 1,
                                "limit": 20,
                                "total": 1,
                                "items": [
                                    {
                                        "id": "3f4f8e0e-c20b-4e5c-a0ee-5845a99759d9",
                                        "user_id": "17cf3f5f-03bb-492a-bbc4-34a6ad4a4353",
                                        "change": 50,
                                        "reason": "ad_reward",
                                        "reference_id": "01c10ea3-18de-4caf-9f63-983f535dfdc0",
                                        "created_at": "2026-10-03T10:00:00Z",
                                    }
                                ],
                            }
                        }
                    }
                }
            },
        }
    },
)
def read_my_ledger(
    page: int = Query(default=1, ge=1, examples=[1]),
    limit: int = Query(default=20, ge=1, le=100, examples=[20]),
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

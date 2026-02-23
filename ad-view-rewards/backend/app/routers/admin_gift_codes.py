import csv
import io
import re

from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from sqlalchemy.orm import Session

from app.core.security import get_current_admin
from app.db.base import get_db
from app.models.gift_code import GiftCode
from app.models.user import User
from app.schemas.gift_code import GiftCodeRead, GiftCodeRedeemRequest, GiftCodeUploadJson

router = APIRouter()

_PROVIDER_PATTERN = re.compile(r"^[a-z][a-z0-9_]{1,49}$")


def _validate_provider(provider: str) -> str:
    normalized = provider.strip().lower()
    if not _PROVIDER_PATTERN.match(normalized):
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Invalid provider")
    return normalized


def _extract_codes_from_csv(raw_csv: str) -> list[str]:
    csv_buffer = io.StringIO(raw_csv)
    reader = csv.DictReader(csv_buffer)
    if reader.fieldnames and "code" in [name.strip().lower() for name in reader.fieldnames]:
        codes: list[str] = []
        for row in reader:
            code = (row.get("code") or "").strip()
            if code:
                codes.append(code)
        return codes

    csv_buffer.seek(0)
    plain_reader = csv.reader(csv_buffer)
    return [row[0].strip() for row in plain_reader if row and row[0].strip()]


def _normalize_and_validate_codes(codes: list[str]) -> list[str]:
    normalized = [code.strip() for code in codes if code.strip()]
    if not normalized:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="No codes provided")

    if len(set(normalized)) != len(normalized):
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Duplicate codes in payload")
    return normalized


@router.post('/gift-codes', response_model=list[GiftCodeRead], status_code=status.HTTP_201_CREATED)
async def upload_gift_codes(
    request: Request,
    provider: str | None = Query(default=None),
    db: Session = Depends(get_db),
    _admin: User = Depends(get_current_admin),
) -> list[GiftCodeRead]:
    content_type = request.headers.get("content-type", "")

    resolved_provider: str | None = provider
    codes: list[str]

    if "text/csv" in content_type:
        raw_csv = (await request.body()).decode("utf-8")
        if not resolved_provider:
            raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="provider is required for CSV upload")
        codes = _extract_codes_from_csv(raw_csv)
    else:
        try:
            payload = await request.json()
        except ValueError as exc:
            raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Invalid JSON payload") from exc
        if isinstance(payload, dict):
            parsed = GiftCodeUploadJson.model_validate(payload)
            resolved_provider = parsed.provider
            codes = parsed.codes
        elif isinstance(payload, list):
            if not resolved_provider:
                raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="provider is required")
            codes = [str(item) for item in payload]
        else:
            raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Invalid JSON payload")

    assert resolved_provider is not None
    provider_value = _validate_provider(resolved_provider)
    normalized_codes = _normalize_and_validate_codes(codes)

    existing_codes = {
        code
        for (code,) in db.query(GiftCode.code).filter(GiftCode.code.in_(normalized_codes)).all()
    }
    if existing_codes:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Duplicate codes already exist")

    created_rows: list[GiftCode] = []
    for code in normalized_codes:
        row = GiftCode(code=code, provider=provider_value)
        db.add(row)
        created_rows.append(row)

    db.commit()
    for row in created_rows:
        db.refresh(row)

    return [GiftCodeRead.model_validate(row) for row in created_rows]


@router.get('/gift-codes', response_model=list[GiftCodeRead])
def list_gift_codes(
    redeemed: bool | None = Query(default=None),
    db: Session = Depends(get_db),
    _admin: User = Depends(get_current_admin),
) -> list[GiftCodeRead]:
    query = db.query(GiftCode)
    if redeemed is not None:
        query = query.filter(GiftCode.redeemed == redeemed)

    rows = query.order_by(GiftCode.created_at.desc()).all()
    return [GiftCodeRead.model_validate(row) for row in rows]


@router.post('/redeem-code', response_model=GiftCodeRead)
def assign_gift_code(
    payload: GiftCodeRedeemRequest,
    db: Session = Depends(get_db),
    _admin: User = Depends(get_current_admin),
) -> GiftCodeRead:
    gift_code = db.query(GiftCode).filter(GiftCode.code == payload.code).first()
    if gift_code is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Gift code not found")

    user = db.query(User).filter(User.id == payload.user_id).first()
    if user is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    gift_code.assigned_to_user_id = payload.user_id
    gift_code.redeemed = False

    db.commit()
    db.refresh(gift_code)

    return GiftCodeRead.model_validate(gift_code)

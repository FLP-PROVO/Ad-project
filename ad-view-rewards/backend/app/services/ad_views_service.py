import uuid
from datetime import datetime, timezone

from sqlalchemy.orm import Session

from app.models.ad_views import AdView


def create_ad_view(db: Session, ad_id: uuid.UUID, viewer_id: uuid.UUID, client_info: dict | None = None) -> AdView:
    ad_view = AdView(
        ad_id=ad_id,
        viewer_id=viewer_id,
        started_at=datetime.now(timezone.utc),
        client_info=client_info,
    )
    db.add(ad_view)
    db.commit()
    db.refresh(ad_view)
    return ad_view


def get_ad_view(db: Session, view_id: uuid.UUID) -> AdView | None:
    return db.query(AdView).filter(AdView.id == view_id).first()

from pathlib import Path

from alembic import command
from alembic.config import Config
from sqlalchemy import create_engine, inspect


def test_alembic_upgrade_creates_ad_views_columns_and_daily_unique_index() -> None:
    backend_dir = Path(__file__).resolve().parents[1]
    sqlite_path = backend_dir / "test_ad_views_migration.db"
    db_url = f"sqlite+pysqlite:///{sqlite_path}"

    cfg = Config(str(backend_dir / "alembic.ini"))
    cfg.set_main_option("sqlalchemy.url", db_url)

    command.upgrade(cfg, "head")

    engine = create_engine(db_url)
    inspector = inspect(engine)

    ad_views_columns = {column["name"] for column in inspector.get_columns("ad_views")}
    assert {
        "id",
        "ad_id",
        "viewer_id",
        "started_at",
        "completed_at",
        "watched_seconds",
        "completion_rate",
        "rewarded",
        "rewarded_points",
        "client_info",
        "created_at",
    }.issubset(ad_views_columns)

    with engine.connect() as conn:
        idx = conn.exec_driver_sql(
            "SELECT name FROM sqlite_master WHERE type='index' AND name='ux_ad_view_user_ad_date'"
        ).fetchone()
    assert idx is not None

    sqlite_path.unlink(missing_ok=True)

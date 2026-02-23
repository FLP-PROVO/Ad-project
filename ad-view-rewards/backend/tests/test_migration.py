from pathlib import Path

from alembic import command
from alembic.config import Config
from sqlalchemy import create_engine, inspect


def test_alembic_upgrade_creates_users_ads_rewards_and_gift_codes_tables() -> None:
    backend_dir = Path(__file__).resolve().parents[1]
    sqlite_path = backend_dir / "test_migration.db"
    db_url = f"sqlite+pysqlite:///{sqlite_path}"

    cfg = Config(str(backend_dir / "alembic.ini"))
    cfg.set_main_option("sqlalchemy.url", db_url)

    command.upgrade(cfg, "head")

    engine = create_engine(db_url)
    inspector = inspect(engine)
    table_names = inspector.get_table_names()
    assert "users" in table_names
    assert "ads" in table_names
    assert "ad_views" in table_names
    assert "points_ledger" in table_names
    assert "gift_codes" in table_names

    sqlite_path.unlink(missing_ok=True)

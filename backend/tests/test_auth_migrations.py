from argparse import Namespace
from io import StringIO
from pathlib import Path

from alembic import command
from alembic.autogenerate import compare_metadata
from alembic.config import Config
from alembic.migration import MigrationContext
import pytest
import sqlalchemy as sa
from sqlalchemy.exc import IntegrityError

from app.core.config import settings
from app.db.session import Base

BACKEND = Path(__file__).resolve().parents[1]


def config(connection=None):
    result = Config(str(BACKEND / "alembic.ini"))
    if connection is not None:
        result.attributes["connection"] = connection
    return result


@pytest.fixture
def legacy_engine(empty_pg_engine):
    legacy = sa.MetaData()
    sa.Table(
        "users", legacy,
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("name", sa.String(100), nullable=False),
        sa.Column("email", sa.String(255), nullable=False, unique=True, index=True),
        sa.Column("password_hash", sa.String(255), nullable=False),
        sa.Column("created_at", sa.DateTime, nullable=False),
    )
    for table in Base.metadata.sorted_tables:
        if table.name != "users":
            table.to_metadata(legacy)
    legacy.create_all(empty_pg_engine)
    with empty_pg_engine.begin() as conn:
        conn.execute(sa.text("INSERT INTO users VALUES (41, 'Legacy', 'legacy@example.com', 'original-hash', CURRENT_TIMESTAMP)"))
        conn.execute(sa.text("INSERT INTO reports (id,user_id,report_name,report_date,upload_date,file_url) VALUES (71,41,'old.pdf',CURRENT_DATE,CURRENT_TIMESTAMP,'old.pdf')"))
        conn.execute(sa.text("INSERT INTO chat_history (id,user_id,report_id,question,answer,timestamp) VALUES (81,41,71,'Question','Answer',CURRENT_TIMESTAMP)"))
    return empty_pg_engine


def upgrade(engine):
    with engine.begin() as conn:
        command.upgrade(config(conn), "head")


def test_upgrade_preserves_legacy_users_reports_and_history(legacy_engine):
    upgrade(legacy_engine)
    with legacy_engine.connect() as conn:
        user = conn.execute(sa.text("SELECT id,email,password_hash,firebase_uid FROM users")).one()
        assert tuple(user) == (41, "legacy@example.com", "original-hash", None)
        assert conn.scalar(sa.text("SELECT user_id FROM reports WHERE id=71")) == 41
        assert conn.scalar(sa.text("SELECT answer FROM chat_history WHERE id=81")) == "Answer"
        columns = {column["name"]: column for column in sa.inspect(conn).get_columns("users")}
        assert columns["password_hash"]["nullable"] is True
        assert columns["firebase_uid"]["nullable"] is True
        assert compare_metadata(MigrationContext.configure(conn), Base.metadata) == []


def test_migration_enforces_uid_uniqueness_and_allows_null_uids(legacy_engine):
    upgrade(legacy_engine)
    with legacy_engine.begin() as conn:
        conn.execute(sa.text("INSERT INTO users (id,name,email,password_hash,created_at) VALUES (42,'Password','password@example.com','hash',CURRENT_TIMESTAMP)"))
        conn.execute(sa.text("INSERT INTO users (id,name,email,firebase_uid,created_at) VALUES (43,'Google','google@example.com','uid',CURRENT_TIMESTAMP)"))
    with pytest.raises(IntegrityError):
        with legacy_engine.begin() as conn:
            conn.execute(sa.text("INSERT INTO users (id,name,email,firebase_uid,created_at) VALUES (44,'Duplicate','duplicate@example.com','uid',CURRENT_TIMESTAMP)"))
    with legacy_engine.connect() as conn:
        assert conn.scalar(sa.text("SELECT count(*) FROM users")) == 3


def test_safe_downgrade_preserves_original_data(legacy_engine):
    upgrade(legacy_engine)
    with legacy_engine.begin() as conn:
        command.downgrade(config(conn), "0001_existing_schema")
    with legacy_engine.connect() as conn:
        columns = {column["name"]: column for column in sa.inspect(conn).get_columns("users")}
        assert "firebase_uid" not in columns
        assert columns["password_hash"]["nullable"] is False
        assert conn.scalar(sa.text("SELECT password_hash FROM users WHERE id=41")) == "original-hash"
        assert conn.scalar(sa.text("SELECT user_id FROM reports WHERE id=71")) == 41
        assert conn.scalar(sa.text("SELECT user_id FROM chat_history WHERE id=81")) == 41


def test_downgrade_refuses_google_only_users_without_any_partial_changes(legacy_engine):
    upgrade(legacy_engine)
    with legacy_engine.begin() as conn:
        conn.execute(sa.text("INSERT INTO users (id,name,email,firebase_uid,created_at) VALUES (43,'Google','google@example.com','uid',CURRENT_TIMESTAMP)"))
    with pytest.raises(RuntimeError, match="Google-only"):
        with legacy_engine.begin() as conn:
            cfg = config(conn)
            cfg.cmd_opts = Namespace(x=["allow_google_unlink=true"])
            command.downgrade(cfg, "0001_existing_schema")
    with legacy_engine.connect() as conn:
        assert conn.scalar(sa.text("SELECT firebase_uid FROM users WHERE id=43")) == "uid"
        assert conn.scalar(sa.text("SELECT version_num FROM alembic_version")) == "0002_google_identity"


def test_downgrade_requires_explicit_acknowledgement_of_link_removal(legacy_engine):
    upgrade(legacy_engine)
    with legacy_engine.begin() as conn:
        conn.execute(sa.text("UPDATE users SET firebase_uid='linked-uid' WHERE id=41"))
    with pytest.raises(RuntimeError, match="discard Google links"):
        with legacy_engine.begin() as conn:
            command.downgrade(config(conn), "0001_existing_schema")
    with legacy_engine.connect() as conn:
        assert conn.scalar(sa.text("SELECT firebase_uid FROM users WHERE id=41")) == "linked-uid"
    with legacy_engine.begin() as conn:
        cfg = config(conn)
        cfg.cmd_opts = Namespace(x=["allow_google_unlink=true"])
        command.downgrade(cfg, "0001_existing_schema")
    with legacy_engine.connect() as conn:
        assert conn.scalar(sa.text("SELECT password_hash FROM users WHERE id=41")) == "original-hash"


def test_baseline_does_not_create_missing_business_tables(empty_pg_engine):
    with pytest.raises(RuntimeError, match="Missing legacy table"):
        upgrade(empty_pg_engine)
    with empty_pg_engine.connect() as conn:
        assert not sa.inspect(conn).has_table("users")


def test_baseline_refuses_schema_drift(legacy_engine):
    with legacy_engine.begin() as conn:
        conn.execute(sa.text("ALTER TABLE users ADD COLUMN unexpected TEXT"))
    with pytest.raises(RuntimeError, match="schema mismatch"):
        upgrade(legacy_engine)
    with legacy_engine.connect() as conn:
        assert "firebase_uid" not in {column["name"] for column in sa.inspect(conn).get_columns("users")}


def test_offline_upgrade_sql_uses_alter_table_without_recreation(monkeypatch):
    monkeypatch.setattr(settings, "DATABASE_URL", "postgresql://unused:unused@localhost/unused")
    cfg = config()
    cfg.output_buffer = StringIO()
    command.upgrade(cfg, "head", sql=True)
    sql = cfg.output_buffer.getvalue()
    assert "ALTER TABLE users ADD COLUMN firebase_uid" in sql
    assert "CREATE TABLE users" not in sql
    assert "DROP TABLE" not in sql
    assert "DROP NOT NULL" in sql
    assert "UNIQUE (firebase_uid)" in sql

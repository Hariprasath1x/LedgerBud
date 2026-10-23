"""Tests for Alembic migrations and PostgreSQL schema compatibility.

Covers:
1. Linear migration history with single head.
2. Full migration from base to head on fresh database (all 11 tables created).
3. Zero schema drift between Alembic head and Base.metadata.
4. Idempotency of upgrading when already at head.
5. Safe downgrade and re-upgrade between revisions.
6. Verification of required columns on wallets, transactions, merchants, and other models.
7. Real PostgreSQL migration execution on an isolated, disposable database if PostgreSQL is available.
8. Database URL normalization (postgres:// -> postgresql://, whitespace trimming).
"""

import os
import tempfile
import pytest
from alembic import command
from alembic.config import Config
from alembic.script import ScriptDirectory
from sqlalchemy import create_engine, inspect

from app.fastapi_app.core.config import Settings
from app.fastapi_app.db.base import Base


EXPECTED_TABLES = {
    "alembic_version",
    "users",
    "wallets",
    "transactions",
    "merchants",
    "budgets",
    "goals",
    "subscriptions",
    "import_jobs",
    "net_worth_items",
    "net_worth_snapshots",
    "fire_analysis",
}


def test_alembic_migration_chain_is_linear():
    """Verify Alembic history has a single head and unbroken down_revision chain."""
    cfg = Config("alembic.ini")
    script = ScriptDirectory.from_config(cfg)
    heads = script.get_heads()
    assert len(heads) == 1, f"Expected single head, got {heads}"
    assert heads[0] == "c2905ef2a301"

    # Walk from head to base
    curr = script.get_revision(heads[0])
    revisions = []
    while curr:
        revisions.append(curr.revision)
        curr = script.get_revision(curr.down_revision) if curr.down_revision else None

    assert revisions == [
        "c2905ef2a301",
        "b1804dc1b57c",
        "0002_create_wallets_and_transactions",
        "0001_create_users_table",
    ]


def test_fresh_migration_creates_all_tables_and_columns():
    """Run full migration chain from empty SQLite database to head and verify complete schema."""
    with tempfile.NamedTemporaryFile(suffix=".db") as tmp:
        db_url = f"sqlite:///{tmp.name}"
        cfg = Config("alembic.ini")
        cfg.set_main_option("sqlalchemy.url", db_url)

        # 1. Upgrade to head
        command.upgrade(cfg, "head")

        engine = create_engine(db_url)
        inspector = inspect(engine)
        actual_tables = set(inspector.get_table_names())
        assert EXPECTED_TABLES.issubset(actual_tables), f"Missing tables: {EXPECTED_TABLES - actual_tables}"

        # 2. Verify wallets columns
        wallet_cols = {c["name"] for c in inspector.get_columns("wallets")}
        assert "is_archived" in wallet_cols

        # 3. Verify transactions columns
        txn_cols = {c["name"] for c in inspector.get_columns("transactions")}
        expected_txn_cols = {
            "is_transfer",
            "transfer_pair_id",
            "merchant_id",
            "raw_description",
            "normalized_description",
            "confidence_score",
            "recognition_source",
            "matching_method",
            "reason_for_decision",
        }
        assert expected_txn_cols.issubset(txn_cols), f"Missing txn cols: {expected_txn_cols - txn_cols}"

        # 4. Verify merchants columns
        merchant_cols = {c["name"] for c in inspector.get_columns("merchants")}
        assert {"unique_identifier", "display_name", "category", "total_transactions", "total_amount"}.issubset(
            merchant_cols
        )

        # 5. Check schema drift against Base.metadata
        command.check(cfg)

        # 6. Idempotent re-upgrade
        command.upgrade(cfg, "head")


def test_migration_downgrade_and_reupgrade():
    """Verify revision c2905ef2a301 can downgrade back to b1804dc1b57c and re-upgrade safely."""
    with tempfile.NamedTemporaryFile(suffix=".db") as tmp:
        db_url = f"sqlite:///{tmp.name}"
        cfg = Config("alembic.ini")
        cfg.set_main_option("sqlalchemy.url", db_url)

        # Upgrade to head
        command.upgrade(cfg, "head")

        # Downgrade to previous revision
        command.downgrade(cfg, "b1804dc1b57c")
        engine = create_engine(db_url)
        inspector = inspect(engine)
        tables_at_prev = set(inspector.get_table_names())
        assert "budgets" not in tables_at_prev
        assert "merchants" not in tables_at_prev

        # Re-upgrade to head
        command.upgrade(cfg, "head")
        inspector = inspect(engine)
        tables_at_head = set(inspector.get_table_names())
        assert EXPECTED_TABLES.issubset(tables_at_head)


def test_database_url_normalization():
    """Test PostgreSQL and MySQL URL normalization and whitespace trimming."""
    # 1. postgres:// -> postgresql://
    s1 = Settings(DATABASE_URL=" postgres://user:secret@db.render.com:5432/ledgerbud ")
    assert s1.database_url == "postgresql://user:secret@db.render.com:5432/ledgerbud"

    # 2. postgresql:// preserved
    s2 = Settings(DATABASE_URL="postgresql://user:secret@localhost:5432/ledgerbud")
    assert s2.database_url == "postgresql://user:secret@localhost:5432/ledgerbud"

    # 3. postgresql+psycopg2:// preserved
    s3 = Settings(DATABASE_URL="postgresql+psycopg2://user:secret@localhost:5432/ledgerbud")
    assert s3.database_url == "postgresql+psycopg2://user:secret@localhost:5432/ledgerbud"

    # 4. sqlite preserved
    s4 = Settings(DATABASE_URL="sqlite:///:memory:")
    assert s4.database_url == "sqlite:///:memory:"


@pytest.fixture
def disposable_pg_db():
    """Create an isolated, disposable PostgreSQL database for migration testing, and drop it on teardown."""
    try:
        import psycopg2
        from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT
    except ImportError:
        pytest.skip("psycopg2 not available")

    db_name = "ledgerbud_pytest_migration_temp"
    try:
        conn = psycopg2.connect(dbname="postgres", connect_timeout=2)
        conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
        cur = conn.cursor()
        cur.execute(f"DROP DATABASE IF EXISTS {db_name};")
        cur.execute(f"CREATE DATABASE {db_name};")
        cur.close()
        conn.close()
    except Exception as exc:
        pytest.skip(f"Local PostgreSQL server not reachable: {exc}")

    pg_url = f"postgresql://localhost/{db_name}"
    yield pg_url

    try:
        conn = psycopg2.connect(dbname="postgres", connect_timeout=2)
        conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
        cur = conn.cursor()
        cur.execute(f"DROP DATABASE IF EXISTS {db_name};")
        cur.close()
        conn.close()
    except Exception:
        pass


def test_postgresql_migration_fresh_and_check(disposable_pg_db):
    """Execute complete Alembic upgrade on a real, fresh PostgreSQL instance and verify zero drift."""
    pg_url = disposable_pg_db
    cfg = Config("alembic.ini")
    cfg.set_main_option("sqlalchemy.url", pg_url)

    # 1. Run upgrade head on fresh PostgreSQL
    command.upgrade(cfg, "head")

    engine = create_engine(pg_url)
    inspector = inspect(engine)
    tables = set(inspector.get_table_names())
    assert EXPECTED_TABLES.issubset(tables), f"Missing tables in PostgreSQL: {EXPECTED_TABLES - tables}"

    # 2. Check columns in PostgreSQL
    wallet_cols = {c["name"] for c in inspector.get_columns("wallets")}
    assert "is_archived" in wallet_cols

    txn_cols = {c["name"] for c in inspector.get_columns("transactions")}
    assert "is_transfer" in txn_cols
    assert "merchant_id" in txn_cols

    # 3. Check zero schema drift on PostgreSQL
    command.check(cfg)

    # 4. Verify idempotent second upgrade
    command.upgrade(cfg, "head")

    # 5. Verify downgrade and re-upgrade on PostgreSQL
    command.downgrade(cfg, "b1804dc1b57c")
    inspector = inspect(engine)
    assert "budgets" not in set(inspector.get_table_names())

    command.upgrade(cfg, "head")
    inspector = inspect(engine)
    assert EXPECTED_TABLES.issubset(set(inspector.get_table_names()))

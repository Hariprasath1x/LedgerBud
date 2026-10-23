"""Alembic environment for the FastAPI SQLAlchemy models."""

from logging.config import fileConfig

from alembic import context
from sqlalchemy import engine_from_config, pool

from app.fastapi_app.core.config import settings
from app.fastapi_app.db.base import Base
from app.fastapi_app.models import (  # noqa: F401 - register model metadata
    Budget,
    FireAnalysis,
    Goal,
    ImportJob,
    Merchant,
    NetWorthItem,
    NetWorthSnapshot,
    Subscription,
    Transaction,
    User,
    Wallet,
)

config = context.config

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# Prioritize explicitly passed sqlalchemy.url (e.g. in tests/CLI) or fallback to settings.database_url
configured_url = config.get_main_option("sqlalchemy.url")
db_url = configured_url if configured_url and "localhost:5432/ledgerbud" not in configured_url else settings.database_url
config.set_main_option("sqlalchemy.url", db_url)
target_metadata = Base.metadata


def run_migrations_offline() -> None:
    url = config.get_main_option("sqlalchemy.url") or settings.database_url
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        render_as_batch=True,
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    section = config.get_section(config.config_ini_section, {}).copy()
    url = config.get_main_option("sqlalchemy.url") or settings.database_url
    section["sqlalchemy.url"] = url
    connectable = engine_from_config(
        section,
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        # PostgreSQL compatibility: ensure alembic_version has sufficient column length
        # for revision IDs longer than 32 characters (e.g. 0002_create_wallets_and_transactions is 36 chars)
        if connection.dialect.name == "postgresql":
            from sqlalchemy import text
            connection.execute(text("""
                CREATE TABLE IF NOT EXISTS alembic_version (
                    version_num VARCHAR(128) NOT NULL PRIMARY KEY
                );
                ALTER TABLE alembic_version ALTER COLUMN version_num TYPE VARCHAR(128);
            """))
            connection.commit()

        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            render_as_batch=True,
        )
        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()

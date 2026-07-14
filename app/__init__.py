"""Shared application package for the legacy Flask UI.

The FastAPI backend now lives under app.fastapi_app. This module stays import-safe
so the new backend can run even when the legacy Flask dependencies are not installed.
"""

from __future__ import annotations

import logging
import os
from typing import Optional

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Optional legacy Flask dependencies — gracefully absent in FastAPI-only envs.
# ---------------------------------------------------------------------------
try:
    from flask import Flask  # type: ignore[import]
    from config import config  # type: ignore[import]
    from app.extensions import db, migrate  # type: ignore[import]
    _FLASK_AVAILABLE = True
except ImportError:  # pragma: no cover
    Flask = None  # type: ignore[assignment,misc]
    config = None  # type: ignore[assignment]
    db = None  # type: ignore[assignment]
    migrate = None  # type: ignore[assignment]
    _FLASK_AVAILABLE = False


def create_app(config_name: Optional[str] = None):
    """Create and configure the legacy Flask application when Flask deps are available."""
    if not _FLASK_AVAILABLE or Flask is None or db is None:
        raise RuntimeError("Legacy Flask dependencies are not installed in this environment.")

    config_name = config_name or os.environ.get('FLASK_ENV', 'development')

    app = Flask(__name__)
    app.config.from_object(config.get(config_name, config['default']))  # type: ignore[index]

    # Ensure upload folder exists
    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

    # Initialize extensions
    db.init_app(app)
    migrate.init_app(app, db)  # type: ignore[union-attr]

    # Register blueprints
    _register_blueprints(app)

    # Register CLI commands
    _register_commands(app)

    # Initialize local development schema automatically so the UI can boot without
    # requiring a separate database setup step.
    _initialize_database(app)

    # Setup logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s [%(levelname)s] %(name)s: %(message)s',
    )

    return app


def _register_blueprints(app) -> None:  # type: ignore[no-untyped-def]
    from app.routes import (  # type: ignore[import]
        dashboard_bp, transactions_bp, wallets_bp,
        budgets_bp, goals_bp, ingestion_bp, analytics_bp,
    )
    app.register_blueprint(dashboard_bp)
    app.register_blueprint(transactions_bp)
    app.register_blueprint(wallets_bp)
    app.register_blueprint(budgets_bp)
    app.register_blueprint(goals_bp)
    if ingestion_bp is not None:
        app.register_blueprint(ingestion_bp)
    app.register_blueprint(analytics_bp)


def _register_commands(app) -> None:  # type: ignore[no-untyped-def]
    @app.cli.command('seed')
    def seed_command():
        """Seed the database with initial data."""
        from app.seeder import seed_all  # type: ignore[import]
        with app.app_context():
            cats, merchants = seed_all()
            print(f'[OK] Seeded {cats} categories and {merchants} merchants.')

    @app.cli.command('create-db')
    def create_db_command():
        """Create all database tables."""
        with app.app_context():
            db.create_all()  # type: ignore[union-attr]
            print('[OK] Database tables created.')
            from app.seeder import seed_all  # type: ignore[import]
            cats, merchants = seed_all()
            print(f'[OK] Seeded {cats} categories and {merchants} merchants.')


def _initialize_database(app) -> None:  # type: ignore[no-untyped-def]
    database_uri = app.config.get('SQLALCHEMY_DATABASE_URI', '')
    if not database_uri.startswith('sqlite'):
        return

    with app.app_context():
        from app import models  # noqa: F401  # type: ignore[import]
        from app.seeder import seed_all  # type: ignore[import]

        db.create_all()  # type: ignore[union-attr]
        seed_all()

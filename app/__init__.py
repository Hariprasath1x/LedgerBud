"""
Flask App Factory
"""
import os
import logging
from flask import Flask
from config import config
from app.extensions import db, migrate

logger = logging.getLogger(__name__)


def create_app(config_name: str = None) -> Flask:
    """Create and configure the Flask application."""
    config_name = config_name or os.environ.get('FLASK_ENV', 'development')

    app = Flask(__name__)
    app.config.from_object(config.get(config_name, config['default']))

    # Ensure upload folder exists
    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

    # Initialize extensions
    db.init_app(app)
    migrate.init_app(app, db)

    # Register blueprints
    _register_blueprints(app)

    # Register CLI commands
    _register_commands(app)

    # Setup logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s [%(levelname)s] %(name)s: %(message)s',
    )

    return app


def _register_blueprints(app: Flask):
    from app.routes import (
        dashboard_bp, transactions_bp, wallets_bp,
        budgets_bp, goals_bp, ingestion_bp, analytics_bp,
    )
    app.register_blueprint(dashboard_bp)
    app.register_blueprint(transactions_bp)
    app.register_blueprint(wallets_bp)
    app.register_blueprint(budgets_bp)
    app.register_blueprint(goals_bp)
    app.register_blueprint(ingestion_bp)
    app.register_blueprint(analytics_bp)


def _register_commands(app: Flask):
    @app.cli.command('seed')
    def seed_command():
        """Seed the database with initial data."""
        from app.seeder import seed_all
        with app.app_context():
            cats, merchants = seed_all()
            print(f'✓ Seeded {cats} categories and {merchants} merchants.')

    @app.cli.command('create-db')
    def create_db_command():
        """Create all database tables."""
        with app.app_context():
            db.create_all()
            print('✓ Database tables created.')
            from app.seeder import seed_all
            cats, merchants = seed_all()
            print(f'✓ Seeded {cats} categories and {merchants} merchants.')

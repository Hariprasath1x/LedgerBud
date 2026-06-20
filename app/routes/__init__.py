from .dashboard import dashboard_bp
from .transactions import transactions_bp
from .wallets import wallets_bp
from .budgets import budgets_bp
from .goals import goals_bp
from .ingestion import ingestion_bp
from .analytics import analytics_bp

__all__ = [
    'dashboard_bp', 'transactions_bp', 'wallets_bp',
    'budgets_bp', 'goals_bp', 'ingestion_bp', 'analytics_bp',
]

"""Legacy Flask extension singletons.

Imported conditionally by app/__init__.py when Flask is available.
These objects are initialized in create_app() via init_app().
"""

from flask_sqlalchemy import SQLAlchemy  # type: ignore[import]
from flask_migrate import Migrate  # type: ignore[import]

db = SQLAlchemy()
migrate = Migrate()

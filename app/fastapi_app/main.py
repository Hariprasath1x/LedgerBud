"""FastAPI application factory and ASGI app instance."""

from dotenv import load_dotenv
load_dotenv()  # Must be first — loads .env into os.environ for all worker processes

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.fastapi_app.api.routes.auth import router as auth_router
from app.fastapi_app.api.routes.transactions import router as transactions_router
from app.fastapi_app.api.routes.wallets import router as wallets_router
from app.fastapi_app.api.routes.health import router as health_router
from app.fastapi_app.api.routes.budgets import router as budgets_router
from app.fastapi_app.api.routes.goals import router as goals_router
from app.fastapi_app.api.routes.subscriptions import router as subscriptions_router
from app.fastapi_app.api.routes.imports import router as imports_router
from app.fastapi_app.api.routes.analytics import router as analytics_router
from app.fastapi_app.core.config import settings
from app.fastapi_app.core.logging import configure_logging
from app.fastapi_app.db.base import Base
from app.fastapi_app.db.session import engine
from app.fastapi_app.exceptions.handlers import register_exception_handlers
from app.fastapi_app.models import Transaction, User, Wallet, Budget, Goal, Subscription, ImportJob, FireAnalysis  # noqa: F401 - ensure model registration
from app.fastapi_app.api.routes.dashboard import router as dashboard_router


@asynccontextmanager
async def lifespan(_: FastAPI):
    if settings.auto_create_tables:
        Base.metadata.create_all(bind=engine)
    yield


def create_app() -> FastAPI:
    configure_logging(settings.log_level)

    app = FastAPI(
        title=f"{settings.app_name} API",
        version="1.0.0",
        description="Production-ready financial foundation for LedgerBud.",
        lifespan=lifespan,
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    register_exception_handlers(app)
    app.include_router(health_router)
    app.include_router(auth_router, prefix=settings.api_v1_prefix)
    app.include_router(wallets_router, prefix=settings.api_v1_prefix)
    app.include_router(transactions_router, prefix=settings.api_v1_prefix)
    app.include_router(dashboard_router, prefix=settings.api_v1_prefix)
    app.include_router(budgets_router, prefix=settings.api_v1_prefix)
    app.include_router(goals_router, prefix=settings.api_v1_prefix)
    app.include_router(subscriptions_router, prefix=settings.api_v1_prefix)
    app.include_router(imports_router, prefix=settings.api_v1_prefix)
    app.include_router(analytics_router, prefix=settings.api_v1_prefix)
    
    from app.fastapi_app.api.routes.net_worth import router as net_worth_router
    from app.fastapi_app.api.routes.insights import router as insights_router
    from app.fastapi_app.api.routes.advisor import router as advisor_router
    from app.fastapi_app.api.routes.fire import router as fire_router
    
    app.include_router(net_worth_router, prefix=settings.api_v1_prefix)
    app.include_router(insights_router, prefix=settings.api_v1_prefix)
    app.include_router(advisor_router, prefix=settings.api_v1_prefix)
    app.include_router(fire_router, prefix=settings.api_v1_prefix)

    @app.get("/", tags=["Meta"])
    def root() -> dict[str, str]:
        return {"service": settings.app_name, "status": "running", "docs": "/docs"}

    return app


app = create_app()

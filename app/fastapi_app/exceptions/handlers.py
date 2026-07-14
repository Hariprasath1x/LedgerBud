"""Global exception handlers for the FastAPI app."""

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from sqlalchemy.exc import IntegrityError, SQLAlchemyError


def register_exception_handlers(app: FastAPI) -> None:
    @app.exception_handler(IntegrityError)
    async def integrity_error_handler(_: Request, exc: IntegrityError) -> JSONResponse:
        return JSONResponse(status_code=409, content={"detail": "Database constraint violated", "error": str(exc.orig)})

    @app.exception_handler(SQLAlchemyError)
    async def sqlalchemy_error_handler(_: Request, exc: SQLAlchemyError) -> JSONResponse:
        return JSONResponse(status_code=500, content={"detail": "Database operation failed", "error": str(exc)})

    @app.exception_handler(RequestValidationError)
    async def validation_error_handler(_: Request, exc: RequestValidationError) -> JSONResponse:
        return JSONResponse(status_code=422, content={"detail": exc.errors()})

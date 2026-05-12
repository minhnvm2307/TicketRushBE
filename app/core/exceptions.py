from fastapi import FastAPI, HTTPException
from fastapi.exceptions import RequestValidationError

from app.core.responses import error_response


class ConflictError(Exception):
    pass


class ExpiredEventError(Exception):
    pass


def register_exception_handlers(app: FastAPI) -> None:
    @app.exception_handler(HTTPException)
    async def http_exception_handler(_, exc: HTTPException):
        return error_response(str(exc.detail), exc.status_code)

    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(_, exc: RequestValidationError):
        return error_response(str(exc.errors()), 422)

    @app.exception_handler(Exception)
    async def unhandled_exception_handler(_, __):
        return error_response("Internal server error", 500)

import asyncio
from enum import Enum
from nats.aio.errors import (
    ErrAuthorization,
    ErrBadSubject,
    ErrConnectionClosed,
    ErrConnectionDraining,
    ErrConnectionReconnecting,
    ErrInvalidUserCredentials,
    ErrMaxPayload,
    ErrNoResponder,
    ErrNoServers,
    ErrStaleConnection,
    NatsError,
    ErrTimeout,
)
from starlette.responses import PlainTextResponse
from starlette.requests import Request
from loguru import logger
from .utils import Subject


def exception_handler(code: int, description: str, error_msg: str | None = None):
    async def http_exception(request: Request, exc: Exception):
        try:
            subject = Subject.from_request(request)
        except Exception:
            subject = request.url.path
        if error_msg:
            logger.error(
                error_msg.format(
                    exc=exc, request=request, subject=subject
                )
            )
        else:
            logger.error(exc)
        return PlainTextResponse(description, code)

    return http_exception


class ExceptionHandlers(Enum):
    InvalidRequestError = exception_handler(400, "Invalid request")
    NoResponderError = exception_handler(
        404, "No responder on subject", "{subject} - {exc}"
    )
    TimeoutError = exception_handler(
        504,
        "Did not receive a timely response from the upstream server",
        "{subject} - {exc}",
    )
    InternalError = exception_handler(500, "Internal server error", "{subject} - {exc}")
    InvalidCredentialsError = exception_handler(
        401, "Invalid credentials", "{subject} - {exc}"
    )
    UnauthorizedError = exception_handler(
        403,"Authorization failed", "{subject} - {exc}" 
    )
    ConnectionError = exception_handler(503, "Service unavailable", "{subject} - {exc}")
    MaxPayloadError = exception_handler(
        413, "Maximum payload exceeded", "{subject} - {exc}"
    )


exception_handlers = {
    asyncio.TimeoutError: ExceptionHandlers.TimeoutError,
    ErrTimeout: ExceptionHandlers.TimeoutError,
    TimeoutError: ExceptionHandlers.TimeoutError,

    ErrBadSubject: ExceptionHandlers.InvalidRequestError,

    ErrNoResponder: ExceptionHandlers.NoResponderError,

    ErrAuthorization: ExceptionHandlers.UnauthorizedError,
    ErrInvalidUserCredentials: ExceptionHandlers.InvalidCredentialsError,

    ErrConnectionReconnecting: ExceptionHandlers.ConnectionError,
    ErrConnectionDraining: ExceptionHandlers.ConnectionError,
    ErrConnectionClosed: ExceptionHandlers.ConnectionError,
    ErrStaleConnection: ExceptionHandlers.ConnectionError,

    ErrNoServers: ExceptionHandlers.ConnectionError,
    ErrMaxPayload: ExceptionHandlers.MaxPayloadError,

    NatsError: ExceptionHandlers.InternalError,
}

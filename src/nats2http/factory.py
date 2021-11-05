import asyncio
from contextlib import asynccontextmanager
from typing import Literal

from loguru import logger

from starlette.applications import Starlette
from starlette.exceptions import ExceptionMiddleware
from starlette.middleware import Middleware
from starlette.middleware.authentication import AuthenticationMiddleware
# from starlette.middleware.sessions import SessionMiddleware
from starlette.requests import Request
from starlette.routing import Route

from nats2http.auth import NATSAnonymousUser, NATSUser, NatsAuthBackend

from nats2http.errors import exception_handlers
from nats2http import settings


class NATSRequest(Request):
    user: NATSUser | NATSAnonymousUser


def create_app():

    # Define handler
    async def handler(request: NATSRequest):
        # Fetch client
        client = request.user.client
        # Dispatch request
        result = await client.dispatch(request)
        # Return HTTP response
        return result.build_response()

    # Define route
    route = Route("/{path:path}", endpoint=handler, methods=["GET", "POST", "PUT"])

    # Define auth backend
    auth_backend = NatsAuthBackend()

    # Define middlewares
    middleware = [
        Middleware(ExceptionMiddleware, handlers=exception_handlers, debug=settings.DEV),
        # Middleware(SessionMiddleware, secret_key="SECRET", max_age=3600, https_only=False), 
        Middleware(AuthenticationMiddleware, backend=auth_backend)
    ]

    # Define lifecycle
    @asynccontextmanager
    async def lifespan(_: Starlette):
        logger.info("Entering application lifespan")
        try:
            yield
        finally:
            pass
        logger.info("Exiting application lifespan")
        return

    # Return Startlette app
    return Starlette(
        lifespan=lifespan,
        middleware=middleware,
        routes=[route],
        debug=settings.DEV,
    )


def start_app(
    root_path: str = "",
    workers: int = 1,
    dev: bool = True,
    http: Literal["auto"] | Literal["h11"] | Literal["httptools"] = "auto",
    loop: Literal["auto"] | Literal["uvloop"] | Literal["asyncio"] = "auto",
):
    import uvicorn
    import os
    # Make sure this environment variable is propagated
    os.environ["DEV"] = str(dev)
    uvicorn.run(
        "nats2http.factory:create_app",
        factory=True,
        loop=loop,
        http=http,
        workers=1 if dev else workers,
        debug=False,
        reload=False,
        root_path=root_path,
    )

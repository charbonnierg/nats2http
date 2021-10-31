import asyncio
from contextlib import asynccontextmanager
from typing import Literal
from starlette.applications import Starlette
from starlette.requests import Request
from starlette.routing import Route

from loguru import logger

from nats2http.client import NATS2HTTPClient
from nats2http.errors import exception_handlers
from nats2http import settings


def create_app():
    # First create a client
    client = NATS2HTTPClient()

    # Define lifespan
    @asynccontextmanager
    async def lifespan(app: Starlette):
        logger.info("Connecting to NATS")
        await client.connect()
        try:
            logger.info("Application ready")
            yield
        except asyncio.CancelledError:
            logger.info("Application shutdown requested")
        finally:
            logger.info("Closing connection to NATS")
            await client.close()
            logger.info("Applican shutdown finished")

    # Define handler
    async def handler(request: Request):
        result = await client.dispatch(request)
        return result.build_response()

    # Define route
    route = Route("/{path:path}", endpoint=handler, methods=["GET", "POST", "PUT"])

    return Starlette(
        routes=[route],
        exception_handlers=exception_handlers,
        lifespan=lifespan,
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
        debug=dev,
        reload=dev,
        root_path=root_path,
    )

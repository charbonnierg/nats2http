import asyncio
import base64
import binascii
from typing import Any, Tuple
from weakref import finalize

from loguru import logger
from starlette.authentication import (
    AuthenticationBackend,
    AuthenticationError,
    SimpleUser,
    AuthCredentials,
    UnauthenticatedUser
)
from starlette.requests import Request
# from .cache import NATS2HTTPClientStore
from .client import NATS2HTTPClient


ANONYMOUS_CLIENT: NATS2HTTPClient | None = None
ANONYMOUS_LOCK = asyncio.Lock()


class NATSAnonymousUser(UnauthenticatedUser):
    def __init__(self, client: NATS2HTTPClient) -> None:
        super().__init__()
        self.client = client


class NATSUser(SimpleUser):
    def __init__(self, username: str, client: NATS2HTTPClient) -> None:
        super().__init__(username)
        self.client = client


class NatsAuthBackend(AuthenticationBackend):

    def __init__(self, max_sessions: int = 1000) -> None:
        super().__init__()
        # self.store = NATS2HTTPClientStore(maxsize=max_sessions)
        self.lock = asyncio.Lock()

    async def get_authorization_header(self, request: Request) -> Tuple[str | None, str]:
        auth = request.headers.get("authorization", None)

        if auth is None:
            return None, ""

        try:
            scheme, credentials = auth.split()
        except ValueError:
            raise AuthenticationError("Invalid Authorization header")

        return scheme.upper(), credentials

    async def anonymous_login(self, **options: Any) -> NATS2HTTPClient:
        global ANONYMOUS_CLIENT

        async with ANONYMOUS_LOCK:
            if ANONYMOUS_CLIENT is None:
                ANONYMOUS_CLIENT = NATS2HTTPClient(**options)
                await ANONYMOUS_CLIENT.connect()
            return ANONYMOUS_CLIENT

    async def basic_login(self, username: str, password: str) -> NATS2HTTPClient:
        client = NATS2HTTPClient(user=username, password=password)
        await client.connect()
        return client

    async def bearer_login(self, token: str) -> NATS2HTTPClient:
        client = NATS2HTTPClient(token=token)
        await client.connect()
        return client

    async def authenticate(self, request: Request) -> AuthCredentials:

        scheme, creds = await self.get_authorization_header(request)

        match scheme:

            case None:
                client = await self.anonymous_login()
                return AuthCredentials([]), NATSAnonymousUser(client)

            case "BASIC":
                logger.trace(f"{request.client} - Attempting to solve Basic Authentication")
                try:
                    decoded = base64.b64decode(creds).decode("ascii")
                    username, _, password = decoded.partition(":")
                except (ValueError, UnicodeDecodeError, binascii.Error) as exc:
                    raise AuthenticationError('Invalid basic auth credentials')
                client = await self.basic_login(username, password)
                finalize(client, asyncio.create_task, client.close())

            case "BEARER":
                logger.trace(f"{request.client} - Attempting to solve Bearer Authentication")
                username = ""
                client = await self.bearer_login(creds)
                finalize(client, asyncio.create_task, client.close())

            case _:
                logger.error(f"Unsupported authorization method: {scheme}. Given creds: {creds}")
                raise AuthenticationError()

        logger.trace(f"{request.client} - Successfull authentication. Client ID: {client.nc._client_id}")
        return AuthCredentials(["authenticated"]), NATSUser(username, client)

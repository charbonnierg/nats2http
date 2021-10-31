from __future__ import annotations

import asyncio
import json
from dataclasses import dataclass
from typing import Any
from nats import connect, NATS
from nats.aio.errors import ErrBadSubject
from starlette.requests import Request
from starlette.responses import Response

from nats2http.utils import Subject


@dataclass
class RequestResult:
    code: int = 200
    data: bytes = b""
    headers: dict[str, str] | None = None
    media_type: str | None = None

    def build_response(self) -> Response:
        return Response(self.data, self.code, self.headers, self.media_type)


class NATS2HTTPClient:
    def __init__(
        self,
        servers: str | list[str] = "nats://localhost:4222",
        max_inflights: int = 100,
        **kwargs: Any
    ) -> None:
        self.nc = NATS()
        if servers:
            kwargs = {**kwargs, "servers": servers}
        self.options = kwargs
        self.max_inflights = max_inflights
        self.semaphore = asyncio.Semaphore(max_inflights)

    async def connect(self, timeout: int | None = 5):
        self.nc = await asyncio.wait_for(
            connect(**self.options),
            timeout=timeout
        )

    async def close(self, timeout: int | None = 30):
        await asyncio.wait_for(
            self.nc.close(),
            timeout=timeout,
        )

    async def dispatch(self, request: Request) -> RequestResult:
        async with self.semaphore:
            if request.url.path == "/":
                raise ErrBadSubject()
            match request.method.upper():
                case "GET":
                    return await self.handle_get_request(request)
                case "PUT":
                    return await self.handle_put_request(request)
                case "POST":
                    return await self.handle_post_request(request)

    async def handle_put_request(self, request: Request) -> RequestResult:
        """Publish a message on NATS according to given HTTP PUT request"""
        # Gather subject
        subject = Subject.from_request(request)
        # Gather body
        body = await request.body()
        # Get request headers
        request_headers = dict(request.headers)
        # Check if there's a reply header
        _reply: str | None = request_headers.pop("reply-subject", None)
        # Create response headers
        response_headers = {}
        # Convert reply if needed and add to response header
        if _reply:
            reply = Subject(_reply)
            response_headers["reply-subject"] = reply
        else:
            reply = None
        # Publish on subject
        await self.nc.publish(subject, body, reply=reply, headers=request_headers)
        # Return result
        return RequestResult(
            204, b"", response_headers, media_type=None
        )

    async def handle_get_request(self, request: Request) -> RequestResult:
        """Perform a request on NATS according to given HTTP GET request"""
        # Gather subject
        subject = Subject.from_request(request)
        # Gather query parameters
        body = dict(request.query_params.items())
        # Fetch timeout
        timeout = request.headers.get("request-timeout", 1)
        # Gather request headers
        request_headers = dict(request.headers)
        # Fire request
        msg = await asyncio.wait_for(
            self.nc.request(
                subject,
                # FIXME: Provide function to serialize to JSON in another module
                json.dumps(body).encode("utf-8"),
                timeout=timeout,
                headers=request_headers,
            ),
            timeout
        )
        response_headers = dict(msg.headers)
        media_type = response_headers.pop("content-type", "application/octet-stream;")
        status_code = response_headers.pop("status-code", 200)
        return RequestResult(
            status_code, data=msg.data, headers=msg.headers, media_type=media_type
        )

    async def handle_post_request(self, request: Request) -> RequestResult:
        """Perform a request on NATS according to given HTTP GET request"""
        subject = Subject.from_request(request)
        # Gather body
        body = await request.body()
        # Fetch timeout
        timeout = request.headers.get("request-timeout", 1)
        # Gather request headers
        request_headers = dict(request.headers)
        # Fire request
        msg = await asyncio.wait_for(
            self.nc.request(
                subject,
                body,
                timeout=timeout,
                headers=request_headers,
            ),
            timeout
        )
        response_headers = dict(msg.headers)
        media_type = response_headers.pop("content-type", "application/octet-stream;")
        status_code = response_headers.pop("status-code", 200)
        return RequestResult(
            status_code, data=msg.data, headers=msg.headers, media_type=media_type
        )

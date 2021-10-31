from __future__ import annotations

import re
from typing import Any, List
from nats.aio.errors import ErrBadSubject
from starlette.requests import Request


class Subject:

    __slots__ = "value", "raw"
    PATTERN = re.compile("^\.?([A-Za-z0-9]+(?:.[A-Za-z0-9]+)*)\.?$")

    def __init__(self, value: str, validate: bool = True) -> None:
        self.raw = value
        if validate:
            self.value = self.validate(value)
        else:
            self.value = value

    def to_path(self, trailing_slash: bool = False) -> str:
        path = self.value.replace(".", "/")
        if trailing_slash:
            path += "/"
        return "/" + path

    @classmethod
    def from_request(cls, request: Request) -> Subject:
        return cls(request.url.path)

    def __str__(self) -> str:
        return self.value

    def __repr__(self) -> str:
        s = self.value
        return f"Subject({s})"

    def __eq__(self, other: Any) -> bool:
        return self.value == other

    def __contains__(self, pattern: str) -> bool:
        return pattern in self.value

    def __bytes__(self) -> bytes:
        return self.value.encode("utf-8")

    def __bool__(self) -> bool:
        return bool(self.value)

    def encode(self, encoding: str = ..., *args: Any, **kwargs: Any) -> bytes:
        return self.value.encode(encoding, *args, **kwargs)
        
    @classmethod
    def validate(cls, value: str) -> str:
        subject = value.replace("/", ".")
        matched = cls.PATTERN.match(subject)
        if matched is None:
            raise ErrBadSubject()
        return matched.groups()[0]

    def tokens(self) -> List[str]:
        return self.value.split(".")

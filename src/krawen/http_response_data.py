from dataclasses import dataclass
from enum import Enum

from yarl import URL

from krawen.async_chunked_reader import AsyncChunkedReader


@dataclass
class HttpResponseData:
    http_version: bytes
    status_code: int
    reason: bytes
    headers: dict[bytes, bytes]
    body: AsyncChunkedReader

    def __post_init__(self):
        self.headers = {key.lower(): value for key, value in self.headers.items()}
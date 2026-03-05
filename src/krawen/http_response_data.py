from dataclasses import dataclass

from krawen.async_chunked_reader import AsyncChunkedReader


@dataclass
class HTTPResponseInfo:
    http_version: str
    status_code: int
    reason: str
    headers: dict[str, bytes]

@dataclass
class HTTPResponseData:
    info: HTTPResponseInfo
    body: AsyncChunkedReader

    def __post_init__(self):
        self.headers = {key.lower(): value for key, value in self.info.headers.items()}

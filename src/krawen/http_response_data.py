from dataclasses import dataclass

from krawen.async_chunked_reader import AsyncChunkedReader


@dataclass
class HTTPResponseInfo:
    http_version: str
    status_code: int
    reason: str
    headers: list[tuple[str, bytes]]

    def __post_init__(self):
        self.headers = [(key.lower(), value) for key, value in self.headers]

    def get_headers(self, key: str) -> list[bytes]:
        return list(
            map(
                lambda header: header[1],
                filter(lambda header: header[0] == key.lower(), self.headers)
            )
        )
    def get_first_header(self, key: str) -> bytes:
        try:
            return self.get_headers(key)[0]
        except IndexError:
            raise KeyError('Passed key does not exist')
    @property
    def content_type(self) -> bytes | None:
        try:
            return self.get_first_header('Content-Type')
        except KeyError:
            return None

@dataclass
class HTTPResponseData:
    info: HTTPResponseInfo
    body: AsyncChunkedReader


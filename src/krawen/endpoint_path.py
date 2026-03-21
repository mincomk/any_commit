from dataclasses import dataclass
from enum import Enum

from yarl import URL


@dataclass
class EndpointPath:
    url: URL
    method: HTTPMethod

    def __post_init__(self):
        if not self.url.path.endswith('/'):
            self.url = self.url / ''

        return self.url.with_path(self.url.path + '/')

    def __hash__(self):
        return hash((self.url, self.method))

class HTTPMethod(str, Enum):
    GET = 'GET'
    HEAD = 'HEAD'
    POST = 'POST'
    PUT = 'PUT'
    DELETE = 'DELETE'
    CONNECT = 'CONNECT'
    OPTIONS = 'OPTIONS'
    TRACE = 'TRACE'
    PATCH = 'PATCH'

    def __str__(self): return self.value

    @classmethod
    def from_name(cls, name: str) -> HTTPMethod:
        for method in HTTPMethod:
            if method.value == name:
                return method

        raise ValueError(f'Passed name "{name}" is invalid')

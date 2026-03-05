from dataclasses import dataclass
from enum import Enum

from yarl import URL


@dataclass
class EndpointPath:
    method: MethodType
    url: URL

class MethodType(str, Enum):
    GET = 'GET'
    HEAD = 'HEAD'
    POST = 'POST'
    PUT = 'PUT'
    DELETE = 'DELETE'
    CONNECT = 'CONNECT'
    OPTIONS = 'OPTIONS'
    TRACE = 'TRACE'
    PATCH = 'PATCH'

    @classmethod
    def from_name(cls, name: str) -> MethodType:
        for method in MethodType:
            if method.value == name:
                return method

        raise ValueError(f'Passed name "{name}" is invalid')

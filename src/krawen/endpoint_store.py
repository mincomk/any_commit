import asyncio
import base64
import json
from abc import abstractmethod, ABC
from xml.sax.saxutils import escape

import aiofiles
from yarl import URL

from krawen.async_file_store import AsyncFileStore
from krawen.endpoint_path import EndpointPath, HTTPMethod
from krawen.http_response_data import HTTPResponseData, HTTPResponseInfo


class DuplicateEndpointError(Exception): ...
class EndpointNotFoundError(Exception): ...


class EndpointStore(ABC): # TODO rename
    """
    얘는 파일 관리 역할은 안함
    """
    @abstractmethod
    async def put_endpoint(self, endpoint_path: EndpointPath, data: HTTPResponseData, auto_update: bool = True): ...
    @abstractmethod
    async def rm_endpoint(self, endpoint_path: EndpointPath): ...
    @abstractmethod
    async def get_endpoint(self, endpoint_path: EndpointPath) -> HTTPResponseData: ...


class JsonEndpointStore(EndpointStore):
    def __init__(self, json_file_path: str, file_store: AsyncFileStore):
        self.json_file_path: str = json_file_path
        self._data: dict[EndpointPath, HTTPResponseInfo] = dict()
        self.file_store: AsyncFileStore = file_store

    type JsonResponseInfo = dict[str, str | tuple[tuple[str, str]]]

    @staticmethod
    def endpoint_path_to_str(endpoint_path: EndpointPath) -> str:
        return f'{endpoint_path.url} {endpoint_path.method}'
    @staticmethod
    def str_to_endpoint_path(text: str) -> EndpointPath:
        return EndpointPath(
            method=HTTPMethod.from_name(text.split(' ')[-1]),
            url=URL(text.split(' ')[0])
        )

    @staticmethod
    def response_info_to_json(response_info: HTTPResponseInfo) -> JsonResponseInfo:
        return {
            'http_version': response_info.http_version,
            'status_code': response_info.status_code,
            'reason': response_info.reason,
            'headers': [
                [key, base64.b64encode(value).decode('ascii')]
                for key, value in response_info.headers
            ]
        }
    @staticmethod
    def json_to_response_info(data: JsonResponseInfo) -> HTTPResponseInfo:
        return HTTPResponseInfo(
            http_version=data['http_version'],
            status_code=int(data['status_code']),
            reason=data['reason'],
            headers=[
                (key, base64.b64decode(value))
                for key, value in data['headers']
            ]
        )


    async def load(self):
        async with aiofiles.open(self.json_file_path, mode='r', encoding='utf-8') as f:
            text = await f.read()
            raw_data: dict[str, str] = json.loads(text)
            self._data = {
                self.str_to_endpoint_path(endpoint): self.json_to_response_info(json.loads(response_data))
                for endpoint, response_data in raw_data.items()
            }

    async def save(self, indent: int | None = None):
        async with aiofiles.open(self.json_file_path, mode='w', encoding='utf-8') as f:
            json_data: dict[str, JsonEndpointStore.JsonResponseInfo] = {
                self.endpoint_path_to_str(endpoint): self.response_info_to_json(response_info)
                for endpoint, response_info in self._data.items()
            }
            text = json.dumps(json_data, ensure_ascii=False, indent=indent)
            await f.write(text)

    async def run_save_job(self):
        asyncio.create_task(self.save())

    async def put_endpoint(self, endpoint_path: EndpointPath, data: HTTPResponseData, auto_update: bool = True):
        if not auto_update and endpoint_path in self._data:
            raise DuplicateEndpointError()

        self._data[endpoint_path] = data.info
        await self.file_store.put_file(self.endpoint_path_to_str(endpoint_path), data.body)

    async def rm_endpoint(self, endpoint_path: EndpointPath):
        del self._data[endpoint_path]

    async def get_endpoint(self, endpoint_path: EndpointPath) -> HTTPResponseData:
        try:
            return HTTPResponseData(
                info=self._data[endpoint_path],
                body=await self.file_store.get_file(self.endpoint_path_to_str(endpoint_path))
            )
        except KeyError:
            raise EndpointNotFoundError()

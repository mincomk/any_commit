import asyncio
import json
from abc import abstractmethod, ABC
import aiofiles
from yarl import URL


class DuplicateURLError(Exception): ...
class URLNotFoundError(Exception): ...


class EndpointStore(ABC): # TODO rename
    """
    얘는 파일 관리 역할은 안함
    """
    @abstractmethod
    async def add_url(self, url: URL, file_path: str, auto_update: bool = True): ...

    @abstractmethod
    async def rm_url(self, url: URL): ...

    @abstractmethod
    async def get_url(self, url: URL) -> str: ...


class JsonEndpointStore(EndpointStore):
    def __init__(self, file_path: str):
        super().__init__()
        self.file_path: str = file_path
        self.data: dict[URL, str] = dict()


    async def load(self):
        async with aiofiles.open(self.file_path, mode='r', encoding='utf-8') as f:
            text = await f.read()
            raw_data: dict[str, str] = json.loads(text)
            self.data = {URL(url): file_path for url, file_path in raw_data.items()}

    async def save(self):
        async with aiofiles.open(self.file_path, mode='w', encoding='utf-8') as f:
            encoded_data = {str(url): file_path for url, file_path in self.data.items()}
            text = json.dumps(encoded_data, ensure_ascii=False, indent=4)
            await f.write(text)

    async def run_save_job(self):
        asyncio.get_running_loop().create_task(self.save())


    async def add_url(self, url: URL, file_path: str, auto_update: bool = True):
        if auto_update:
            self.data[url] = file_path
        else:
            if url not in self.data:
                self.data[url] = file_path
            else:
                raise DuplicateURLError()

        await self.run_save_job()

    async def rm_url(self, url: URL):
        try:
            self.data.pop(url)
        except KeyError:
            raise URLNotFoundError()

        await self.run_save_job()

    async def get_url(self, url: URL) -> str:
        try:
            return self.data[url]
        except KeyError:
            raise URLNotFoundError()
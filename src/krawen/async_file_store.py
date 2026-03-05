import hashlib
import os
import urllib.parse
from abc import ABC, abstractmethod
from pathlib import Path

import aiofiles

from krawen.async_chunked_reader import AsyncChunkedReader, AsyncChunkedFileReader


class AsyncFileStore(ABC):
    @abstractmethod
    async def put_file(self, key: str, data: AsyncChunkedReader): ...
    @abstractmethod
    async def get_file(self, key: str) -> AsyncChunkedReader: ...
    @abstractmethod
    async def rm_file(self, key: str): ...

class AsyncLocalFileStore(AsyncFileStore):
    def __init__(self, directory_path: str):
        self.path: Path = Path(directory_path)

    @staticmethod
    def encode(text: str, max_len: int = 255, hash_len: int = 16) -> str:
        h = hashlib.md5(text.encode()).hexdigest()[:hash_len]
        readable_encoded = urllib.parse.quote(text, safe='')
        readable_encoded = readable_encoded[:max_len - hash_len - 1]

        return f'{readable_encoded}_{h}'

    def get_file_path(self, key: str) -> str:
        return str(self.path / (self.encode(key, max_len=240) + '.bin'))


    async def put_file(self, key: str, data: AsyncChunkedReader):
        await data.open()

        async with aiofiles.open(self.get_file_path(key), 'wb') as f:
            while True:
                chunk = await data.read_next_chunk()

                if not chunk:
                    break

                await f.write(chunk)

    async def get_file(self, key: str) -> AsyncChunkedReader:
        return AsyncChunkedFileReader(self.get_file_path(key))

    async def rm_file(self, key: str):
        try:
            os.remove(self.get_file_path(key))
        except FileNotFoundError:
            raise FileNotFoundError(f'File for key "{key}" is not found')

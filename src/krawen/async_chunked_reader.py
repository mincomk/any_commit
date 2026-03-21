import os
from abc import ABC, abstractmethod
from typing import AsyncIterator

import aiofiles
from aiofiles.threadpool.binary import AsyncBufferedReader
from aiohttp import ClientResponse


DEFAULT_CHUNK_SIZE = 8192

class AsyncChunkedReader(ABC, AsyncIterator[bytes]):
    @abstractmethod
    async def read_next_chunk(self) -> bytes:
        """
        if pointer is reached end, it should return None
        """

    @property
    @abstractmethod
    def chunk_size(self) -> int:
        """
        return chunk size as bytes
        """
    @property
    @abstractmethod
    def total_size(self) -> int:
        """
        return total size as bytes
        """


class AsyncChunkedFileReader(AsyncChunkedReader):
    def __init__(self, file: AsyncBufferedReader, chunk_size: int = DEFAULT_CHUNK_SIZE):
        # aiofiles types are weird..
        self._file: AsyncBufferedReader = file
        self._chunk_size: int = chunk_size

    @classmethod
    async def open(cls, path: str, chunk_size: int = DEFAULT_CHUNK_SIZE):
        file = await aiofiles.open(path, 'rb')
        return cls(file, chunk_size)

    async def read_next_chunk(self) -> bytes:
        return await self._file.read(self._chunk_size)
    async def __anext__(self) -> bytes:
        data = await self.read_next_chunk()

        if len(data) == 0:
            raise StopAsyncIteration()
        else:
            return data

    @property
    def chunk_size(self) -> int: return self._chunk_size
    @property
    def total_size(self) -> int: return os.fstat(self._file.fileno()).st_size

class AsyncClientResponseContentReader(AsyncChunkedReader):
    def __init__(self, client_response: ClientResponse, chunk_size: int = DEFAULT_CHUNK_SIZE):
        self._chunk_iterator: AsyncIterator[bytes] = \
            client_response.content.iter_chunked(DEFAULT_CHUNK_SIZE)
        self._chunk_size = chunk_size
        self._total_size = client_response.content.total_bytes

    async def read_next_chunk(self) -> bytes:
        try:
            return await anext(self._chunk_iterator)
        except StopAsyncIteration:
            return bytes()

    async def __anext__(self):
        data = await self.read_next_chunk()

        if len(data) == 0:
            raise StopAsyncIteration()
        else:
            return data

    @property
    def chunk_size(self) -> int: return self._chunk_size
    @property
    def total_size(self) -> int: return self._total_size
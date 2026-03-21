from typing import AsyncIterator
import aiofiles


async def read_in_chunks(file_path: str, chunk_size: int = 1024) -> AsyncIterator[bytes]:
    async with aiofiles.open(file_path, "rb") as f:
        while True:
            chunk = await f.read(chunk_size)
            if not chunk:
                break
            yield chunk
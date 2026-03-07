import asyncio
import os

from yarl import URL

from krawen.async_file_store import AsyncLocalFileStore
from krawen.endpoint_store import JsonEndpointStore
from krawen import KrawenCrawler, EndpointPath, HTTPMethod

os.makedirs('./run/store', exist_ok=True)

file_store = AsyncLocalFileStore('./run/store')
endpoint_store = JsonEndpointStore('./run/endpoints.json', file_store=file_store)

crawler = KrawenCrawler(endpoint_store=endpoint_store)

async def main():
    async with crawler:
        endpoint_path = EndpointPath(
            url=URL('https://example.com'),
            method=HTTPMethod.GET
        )

        await crawler.download(endpoint_path)
        await endpoint_store.save(indent=4)

if __name__ == '__main__':
    asyncio.run(main())


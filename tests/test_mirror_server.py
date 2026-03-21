import asyncio
import os

from yarl import URL

from krawen import KrawenMirrorServer
from krawen.async_file_store import AsyncLocalFileStore
from krawen.endpoint_store import JsonEndpointStore

os.makedirs('./run/store', exist_ok=True)

file_store = AsyncLocalFileStore('./run/store')
endpoint_store = JsonEndpointStore('./run/endpoints.json', file_store=file_store)

mirror_server = KrawenMirrorServer(
    root_origin_url=URL('http://example.com'),
    endpoint_store=endpoint_store
)

async def main():
    mirror_server.setup()
    await endpoint_store.load()
    await mirror_server.start()

if __name__ == '__main__':
    asyncio.run(main())
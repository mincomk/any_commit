import asyncio
import os

from yarl import URL

from krawen import EndpointPath, MethodType, HttpResponseData, HttpResponseInfo
from krawen.async_chunked_reader import AsyncChunkedFileReader
from krawen.endpoint_store import JsonEndpointStore
from krawen.async_file_store import AsyncLocalFileStore

os.makedirs('./run/store', exist_ok=True)

with open('./run/example.html', 'w') as f:
    f.write('This is example content')

file_store = AsyncLocalFileStore('./run/store')
endpoint_store = JsonEndpointStore('./run/endpoints.json', file_store=file_store)

async def main():
    await endpoint_store.put_endpoint(
        endpoint_path=EndpointPath(
            method=MethodType.GET,
            url=URL('https://example.com')
        ),
        data=HttpResponseData(
            info=HttpResponseInfo(
                http_version='1.0',
                status_code=200,
                reason='OK',
                headers={}
            ),
            body=AsyncChunkedFileReader('./run/example.html')
        )
    )

    await endpoint_store.save()

if __name__ == '__main__':
    asyncio.run(main())
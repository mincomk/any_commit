import asyncio
import os
from asyncio import Task

from yarl import URL
import dotenv

from krawen import KrawenCrawler, KrawenMirrorServer, EndpointPath, HTTPMethod
from krawen.async_file_store import AsyncLocalFileStore
from krawen.endpoint_store import JsonEndpointStore
from krawen.krawen_crawler import URLOutOfBoundError, URLNotAbsoluteError

dotenv.load_dotenv()
os.makedirs('./run/store', exist_ok=True)

root_origin_url = URL(os.getenv('KRAWEN_ROOT_HOST_URL'))

file_store = AsyncLocalFileStore('./run/store')
endpoint_store = JsonEndpointStore('./run/endpoints.json', file_store=file_store)

crawler = KrawenCrawler(root_origin_url=root_origin_url, endpoint_store=endpoint_store)
mirror_server = KrawenMirrorServer(root_origin_url=root_origin_url, endpoint_store=endpoint_store)

waiting_requests: set[EndpointPath] = {
    EndpointPath(
        url=root_origin_url,
        method=HTTPMethod.GET
    )
}
running_tasks: set[Task] = set()


async def auto_save():
    while True:
        await endpoint_store.save(indent=4)
        await asyncio.sleep(5)

async def processing_request(endpoint_path: EndpointPath):
    try:
        response_info = await crawler.download(endpoint_path)
    except URLOutOfBoundError:
        print(f'Url "{endpoint_path.url}" is out of bound')
        return
    except URLNotAbsoluteError:
        print(f'Url "{endpoint_path.url}" is not absolute')
        return

    if crawler.is_page(response_info):
        # sub_requests = await crawler.get_network_requests(endpoint_path.url)
        sub_urls = await crawler.get_page_sub_urls(endpoint_path.url)

        new_found_requests = [
            EndpointPath(url=url, method=HTTPMethod.GET) for url in sub_urls
        ]

        waiting_requests.update(new_found_requests)

async def recursive_crawling():
    while True:
        for endpoint_path in waiting_requests:
            task = asyncio.create_task(processing_request(endpoint_path))
            task.add_done_callback(running_tasks.discard)

            running_tasks.add(task)

        started_tasks = len(waiting_requests)
        waiting_requests.clear()

        print(f'{started_tasks} tasks are started')
        print(f'{len(running_tasks)} tasks are currently running')
        print()

        await asyncio.sleep(0.1)


async def main():
    await endpoint_store.load()

    async with crawler:
        crawling_task = asyncio.create_task(recursive_crawling())
        server_task = asyncio.create_task(mirror_server.start())
        auto_save_task = asyncio.create_task(auto_save())

        await crawling_task
        server_task.cancel()
        auto_save_task.cancel()

if __name__ == '__main__':
    asyncio.run(main())

import asyncio
import logging
import os.path
from asyncio import Task

import aiofiles
import bs4
import h11
from aiohttp import ClientSession, NonHttpUrlClientError
from multidict import MultiDictProxy
from playwright.async_api import Playwright, async_playwright
from yarl import URL

from krawen import EndpointPath, HTTPResponseData
from krawen.async_chunked_reader import AsyncClientResponseContentReader
from krawen.endpoint_store import EndpointStore
from krawen.http_response_data import HTTPResponseInfo
from krawen.utils import parsing_utils


class URLOutOfBoundError(Exception): ...
class NotHTMLPageError(Exception): ...


class Crawler:
    def __init__(
            self,
            root_host_url: URL | str | None,
            endpoint_store: EndpointStore,
    ):
        self.root_origin_url: URL | None = None
        try:
            converted_host_url = URL(root_host_url)
            self.root_origin_url: URL = converted_host_url.origin()
        except TypeError: pass

        self.endpoint_store: EndpointStore = endpoint_store

        self.playwright: Playwright | None = None
        self.http_client: ClientSession | None = None


    async def start(self):
        self.playwright = await async_playwright().start()
        self.http_client = ClientSession()

    async def stop(self):
        await self.playwright.stop()
        await self.http_client.close()
        self.playwright = None
        self.http_client = None

    async def __aenter__(self):
        await self.start()

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.stop()


    async def download(self, endpoint_path: EndpointPath):
        if not self.should_download(endpoint_path.url):
            raise URLOutOfBoundError()

        async with self.http_client.request(url=endpoint_path.url, method=endpoint_path.method.value) as response:
            response_info = HTTPResponseInfo(
                http_version=f'{response.version.major}.{response.version.minor}',
                status_code=response.status,
                reason=response.reason,
                headers=[
                    (key, value.encode('latin-1'))
                    for key in response.headers.keys()
                    for value in response.headers.getall(key)
                ]
            )

            await self.endpoint_store.put_endpoint(
                endpoint_path,
                HTTPResponseData(
                    info=response_info,
                    body=AsyncClientResponseContentReader(response)
                )
            )


    async def download_page(self, page_url: URL | str, recursive: bool = True):
        if self.playwright is None:
            raise RuntimeError('Crawler is not started. call start() method first')

        page_url = URL(page_url)

        async with self.http_client.head(page_url) as res:
            if res.headers.get('Content-Type').split(';')[0] != 'text/html':
                raise NotHTMLPageError('Given url is not a HTML page')

        if self.is_child_url(page_url):
            try:
                logging.info(f'Downloading page: "{page_url}" ...')
                await self.download_single_url(page_url)
                logging.info(f'Page downloaded: "{page_url}" ...')
            except Exception:
                logging.exception(f'Page download: "{page_url}" is failed. ignored error:')

        if not recursive:
            return

        logging.info(f'Downloading source files in: "{page_url}"')

        download_tasks: list[Task] = list()
        downloaded_urls: set[URL] = set()
        requested_urls: list[URL] = list()

        browser = await self.playwright.chromium.launch()
        page = await browser.new_page()
        page.on(
            'request',
            lambda req: requested_urls.append(self.convert_absolute_url(req.url))
        )

        await page.goto(str(page_url))
        # 페이지 끝까지 스크롤 돌리는거
        await page.evaluate("""
            async () => {
                await new Promise(resolve => {
                    const distance = 500;
                    const timer = setInterval(() => {
                        window.scrollBy(0, distance);
                        if ((window.innerHeight + window.scrollY) >= document.body.scrollHeight) {
                            clearInterval(timer);
                            resolve();
                        }
                    }, 200);
                });
            }
        """)

        loading_task = asyncio.create_task(page.wait_for_load_state("networkidle"))

        while (not loading_task.done()) or requested_urls:
            try:
                url = requested_urls.pop()
            except IndexError:
                await asyncio.sleep(0.01)
                continue

            if url in downloaded_urls:
                await asyncio.sleep(0.01)
                continue

            if self.is_child_url(url):
                download_tasks.append(asyncio.create_task(self.download_source_file(url)))
            else:
                await asyncio.sleep(0.01)

        # 해당 페이지에 외부 소스로 이어지는 링크 전부 추출
        html = await page.content()

        soup = bs4.BeautifulSoup(html, features='html.parser')
        urls: set[URL] = set()

        for tag in soup.find_all(True):
            attrs = tag.attrs

            for key, value in attrs.items():
                urls.update(
                    map(self.convert_absolute_url, parsing_utils.parse_urls_from_tag_attr(key, value))
                )

        # 페에지에서 뽑은 링크중에 아까 이미 받은건 제외
        urls = urls - downloaded_urls

        for url in urls:
            if self.is_child_url(url):
                asyncio.create_task(self.download_source_file(url))
            else:
                await asyncio.sleep(0.01)

        for task in download_tasks:
            await task

        logging.info(f'Downloading page & source file is done: "{page_url}"')

    async def download_single_url(self, url: URL):
        if not self.is_child_url(url):
            raise URLOutOfBoundError()


        async with self.http_client.get(url) as res:
            content_type = res.headers.get('Content-Type').split(';')[0]
            ext = parsing_utils.guess_extension(content_type)

            if ext is None:
                ext = '.bin'
                logging.warn(f'Unknown Content-type: "{content_type}". instead ".bin" used')

            file_name = self.url_encoder(str(url)) + ext
            file_path = os.path.join(self.source_store_path, file_name)

            async with aiofiles.open(file_path, 'wb') as f:
                async for chunk in res.content.iter_chunked(1024):
                    await f.write(chunk)

            await self.endpoint_store.put_endpoint(url, file_name)


    async def download_source_file(self, url: URL):
        try:
            logging.debug(
                f'Download source file: "{url}" ...')  # , download_single_url, html 문서에서 타 페에지로 이어지는 링크들 어떻게 추출함?
            await self.download_single_url(url)
            logging.debug(f'Source file downloaded: "{url}"')
        except NonHttpUrlClientError:
            pass
        except Exception:
            logging.warning(f'Source file download: "{url}" is failed. ignored error:', exc_info=True)

    def is_child_url(self, url: URL) -> bool:
        if not url.is_absolute():
            return True

        else:
            return url.host == self.root_origin_url.host

    def convert_absolute_url(self, url: URL | str) -> URL:
        url = URL(url)
        if not url.is_absolute():
            return self.root_origin_url.join(url)
        else:
            return url

    def should_download(self, url: URL) -> bool:
        if self.root_origin_url is None:
            return True
        else:
            return url.origin() == self.root_origin_url
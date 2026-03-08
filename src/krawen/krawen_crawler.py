import bs4
from aiohttp import ClientSession
from playwright.async_api import Playwright, async_playwright, Browser, ViewportSize
from playwright.async_api import Request
from yarl import URL

from krawen.endpoint_path import HTTPMethod
from krawen.async_chunked_reader import AsyncClientResponseContentReader
from krawen.endpoint_path import EndpointPath
from krawen.endpoint_store import EndpointStore
from krawen.http_response_data import HTTPResponseData
from krawen.http_response_data import HTTPResponseInfo
from krawen.utils import parse_urls_from_tag_attr, to_absolute_url


class URLOutOfBoundError(Exception): ...
class NotHTMLPageError(Exception): ...


class KrawenCrawler:
    def __init__(
            self,
            endpoint_store: EndpointStore,
            root_origin_url: URL | None = None,
    ):
        self.root_origin_url: URL | None = None

        if root_origin_url is not None:
            self.root_origin_url: URL = root_origin_url.origin()

        self.endpoint_store: EndpointStore = endpoint_store

        self.playwright: Playwright | None = None
        self.browser: Browser | None = None
        self.http_client: ClientSession | None = None


    async def start(self):
        self.playwright = await async_playwright().start()
        self.browser = await self.playwright.firefox.launch()
        self.http_client = ClientSession()

    async def stop(self):
        await self.playwright.stop()
        await self.browser.close()
        await self.http_client.close()
        self.playwright = None
        self.browser = None
        self.http_client = None

    async def __aenter__(self):
        await self.start()

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.stop()


    async def download(self, endpoint_path: EndpointPath) -> HTTPResponseInfo:
        if not self.should_download(endpoint_path.url):
            raise URLOutOfBoundError(f'URL "{endpoint_path.url}" : {endpoint_path.method} is out of processing bound')

        async with self.http_client.request(
                url=endpoint_path.url,
                method=endpoint_path.method.value,
                auto_decompress=False
        ) as response:
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

            return response_info

    async def get_page_sub_urls(self, target_url: URL) -> list[URL]:
        async with self.http_client.get(target_url) as response:
            urls: list[URL] = list()
            html = await response.content.read()
            soup = bs4.BeautifulSoup(html, features='html.parser')

            for tag in soup.find_all(True):
                attrs = tag.attrs

                for key, value in attrs.items():
                    urls.extend(map(
                        lambda u: to_absolute_url(target_url, URL(u)),
                        parse_urls_from_tag_attr(key, value)
                    ))

            return urls


    async def get_network_requests(self, target_url: URL) -> list[EndpointPath]:
        network_requests: list[EndpointPath] = list()
        context = await self.browser.new_context(
            viewport=ViewportSize(width=1920, height=2160)
        )
        page = await context.new_page()

        async def on_request(request: Request):
            network_requests.append(EndpointPath(
                url=to_absolute_url(self.root_origin_url, URL(request.url)),
                method=HTTPMethod.from_name(request.method)
            ))
        page.on('request', on_request)

        await page.goto(str(target_url))

        await page.evaluate(
            """
            async () => {
                await new Promise(resolve => {
                    const timer = setInterval(() => {
                        window.scrollBy(0, 500);
                        if ((window.innerHeight + window.scrollY) >= document.body.scrollHeight) {
                            clearInterval(timer);
                            resolve();
                        }
                    }, 50);
                });
            }
            """
        )

        await page.wait_for_load_state('networkidle')

        await page.close()
        await context.close()

        return network_requests


    def should_download(self, url: URL) -> bool:
        if self.root_origin_url is None:
            return True
        else:
            return url.origin() == self.root_origin_url

    @staticmethod
    def is_page(response_info: HTTPResponseInfo) -> bool:
        try:
            if response_info.get_first_header('Content-Disposition') == b'attachment':
                return False
        except KeyError: pass

        page_headers = [b'text/html', b'application/xhtml+xml']
        target_header = response_info.get_first_header('Content-Type')

        for comparing_header in page_headers:
            if comparing_header in target_header:
                return True

        return False

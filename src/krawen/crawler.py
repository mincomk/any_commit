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


class URLOutOfBoundError(Exception): ...
class NotHTMLPageError(Exception): ...


class Crawler:
    def __init__(
            self,
            endpoint_store: EndpointStore,
            root_host_url: URL | str | None = None,
    ):
        self.root_origin_url: URL | None = None
        try:
            converted_host_url = URL(root_host_url)
            self.root_origin_url: URL = converted_host_url.origin()
        except TypeError: pass

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

            return response_info

    async def download_page_or_file(self, endpoint_path: EndpointPath, recursive: bool = False):
        response_info = await self.download(endpoint_path)


        if self.is_page(response_info) and recursive:
            request_list: list[EndpointPath] = list()
            context = await self.browser.new_context(
                viewport=ViewportSize(width=1920, height=2160)
            )
            page = await context.new_page()

            async def on_request(request: Request):
                request_list.append(EndpointPath(
                    url=URL(request.url),
                    method=HTTPMethod.from_name(request.method)
                ))

            page.on('request', on_request)

            await page.goto(str(endpoint_path.url))

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

            for request in request_list:
                print(request)

            await page.close()
            await context.close()


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

        return response_info.get_first_header('Content-Type') in \
            [b'text/html', b'application/xhtml+xml']
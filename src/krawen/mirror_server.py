import uvicorn
from fastapi import FastAPI, APIRouter, Request, HTTPException
from fastapi.responses import StreamingResponse
from yarl import URL

from krawen import EndpointPath, HTTPMethod
from krawen.endpoint_store import EndpointStore, EndpointNotFoundError
from krawen.utils import to_absolute_url


class MirrorServer:
    def __init__(
            self,
            root_origin_url: URL | str,
            endpoint_store: EndpointStore,
            api_host: str = '0.0.0.0',
            api_port: int = 8000
    ):
        self.app = FastAPI()
        self.root_origin_url: URL = URL(root_origin_url).origin()
        self.endpoint_store: EndpointStore = endpoint_store

        self.api_host: str = api_host
        self.api_port: int = api_port

    def setup(self):
        router = APIRouter()
        router.add_api_route(
            '/{path:path}',
            self.on_route,
            methods=[
                'GET', 'HEAD', 'POST', 'PUT', 'DELETE', 'CONNECT', 'OPTIONS', 'TRACE', 'PATCH'
            ]
        )
        self.app.include_router(router)

    async def start(self):
        config = uvicorn.Config(
            self.app,
            host=self.api_host,
            port=self.api_port,
            log_config=None,
            loop='asyncio'
        )
        server = uvicorn.Server(config)
        await server.serve()

    async def on_route(self, request: Request):
        endpoint_path = EndpointPath(
            url=self.to_original_url(URL(request.url)),
            method=HTTPMethod.from_name(request.method)
        )
        try:
            response_data = await self.endpoint_store.get_endpoint(endpoint_path)
        except EndpointNotFoundError:
            raise HTTPException(status_code=404)

        headers = [(key, value.decode('latin-1')) for key, value in response_data.info.headers]

        return StreamingResponse(
            response_data.body,
            headers=headers,
            status_code=response_data.info.status_code
        )

    def to_original_url(self, url: URL) -> URL:
        return to_absolute_url(self.root_origin_url, url)

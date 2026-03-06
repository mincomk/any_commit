import mimetypes
import os.path
from collections.abc import Callable
from typing import Awaitable
import aiofiles
import uvicorn
from fastapi import FastAPI, APIRouter, Response, Request, HTTPException
from fastapi.responses import StreamingResponse
from yarl import URL

from krawen.endpoint_store import EndpointStore, EndpointNotFoundError
# from krawen.utils import is_text_content_type
from krawen.utils.file import read_in_chunks


async def default_not_found_handler(url: URL) -> str: pass


class MirrorServer:
    def __init__(
            self,
            root_origin_url: URL | str,
            source_store_path: str,
            url_manager: EndpointStore,
            not_found_handler: Callable[[URL], Awaitable[None]] = default_not_found_handler
    ):
        self.app = FastAPI()
        self.root_origin_url: URL = URL(root_origin_url)
        self.source_store_path: str = source_store_path
        self.url_manager: EndpointStore = url_manager
        self.not_found_handler: Callable[[URL], Awaitable[None]] = not_found_handler

    def setup(self):
        router = APIRouter()
        router.add_api_route('/{path:path}', self.on_route, methods=["GET", "POST", "PUT", "DELETE", "PATCH"])
        self.app.include_router(router)

    async def on_route(self, request: Request):
        relative_url = URL(URL(str(request.url)).raw_path_qs)
        url = self.root_origin_url.join(relative_url)

        try:
            file_name = await self.url_manager.get_url(url)
        except EndpointNotFoundError:
            await self.not_found_handler(url)
            raise HTTPException(status_code=404)

        file_path = os.path.join(self.source_store_path, file_name)
        content_type, _ = mimetypes.guess_type(file_name)

        if "TODO":
            async with aiofiles.open(file_path, 'r', encoding='utf-8') as f:
                body = await f.read()
                return Response(content=body, media_type=content_type)

        else:
            return StreamingResponse(read_in_chunks(file_path), media_type=content_type)

    async def run(self, host: str = '127.0.0.1', port=8000):
        config = uvicorn.Config(app=self.app, host=host, port=port)
        server = uvicorn.Server(config=config)
        await server.serve()
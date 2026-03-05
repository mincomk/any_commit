import asyncio
import logging
import os
from json import JSONDecodeError
import dotenv

import krawen
from krawen.endpoint_store import JsonEndpointStore

krawen.utils.setup_logging(level=logging.DEBUG) # To show download log of each files
dotenv.load_dotenv()

source_store_path = os.getenv('SOURCE_STORE_PATH')
root_url = os.getenv('ROOT_URL')
data_file_path = os.getenv('DATA_FILE_PATH')

os.makedirs(source_store_path, exist_ok=True)
url_manager = JsonEndpointStore(data_file_path)

try:
    asyncio.run(url_manager.load())
except (JSONDecodeError, FileNotFoundError):
    asyncio.run(url_manager.save())

crawler = krawen.Crawler(
    'https://buma.wiki',
    source_store_path,
    url_manager
)


async def main():
    async with crawler:
        await crawler.download_page('https://buma.wiki')

asyncio.run(main())
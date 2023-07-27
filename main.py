import os
from asyncio import sleep

import aiohttp
import asyncio
import aiofiles
import math
import tqdm
from yarl import URL
import tempfile

BUFFER_SIZE = 1024 * 10  # Buffer size for the download buffer
tmp_folder_path = tempfile.gettempdir()


async def get_file_size(url):
    async with aiohttp.ClientSession() as session:
        async with session.head(url) as response:
            return int(response.headers.get('Content-Length', 0))


async def get_filename_from_url(url):
    parsed_url = URL(url)
    filename = parsed_url.name
    return filename


async def download_chunk(url, session, start, end, progress_bar, filename):
    headers = {'Range': f'bytes={start}-{end}'}
    async with session.get(url, headers=headers) as response:
        buffer = bytearray()
        async with aiofiles.open(os.path.join(tmp_folder_path, f'chunk_{filename}_{start}-{end}'), 'wb') as f:
            async for chunk in response.content.iter_chunked(BUFFER_SIZE):
                buffer.extend(chunk)
                progress_bar.update(len(chunk))
                if len(buffer) >= BUFFER_SIZE:
                    await f.write(buffer)
                    buffer.clear()
            if buffer:
                await f.write(buffer)


async def merge_chunks(filename, chunks, progress_bar):
    # file_size = sum(os.path.getsize(chunk) for chunk in chunks)
    async with aiofiles.open(filename, 'wb') as f:
        for chunk in chunks:
            async with aiofiles.open(chunk, 'rb') as chunk_file:
                await f.write(await chunk_file.read())
            progress_bar.update(os.path.getsize(chunk))
            os.remove(chunk)
    await sleep(1)
    print(f"{filename} downloaded !")


async def download_manager(url, num_chunks):
    async with aiohttp.ClientSession() as session:
        file_size = await get_file_size(url)
        filename = await get_filename_from_url(url)
        chunk_size = math.ceil(file_size / num_chunks)

        tasks = []
        with tqdm.tqdm(total=file_size, unit='B', unit_scale=True, desc='Downloading', colour='green', leave=False) as pbar:
            for i in range(num_chunks):
                start = i * chunk_size
                end = min(start + chunk_size - 1, file_size - 1)
                task = asyncio.create_task(download_chunk(url, session, start, end, pbar, filename))
                tasks.append(task)

            await asyncio.gather(*tasks)

        chunks = [os.path.join(tmp_folder_path, f'chunk_{filename}_{i * chunk_size}-{min((i + 1) * chunk_size - 1, file_size - 1)}') for i in range(num_chunks)]
        with tqdm.tqdm(total=file_size, unit='B', unit_scale=True, desc='Merging', colour='red', leave=False) as merge_pbar:
            await merge_chunks(filename, chunks, merge_pbar)


if __name__ == "__main__":
    # Take user input for URL and number of chunks
    url = input("Enter the URL: ")
    num_chunks = int(input("Enter the number of chunks: "))

    loop = asyncio.get_event_loop()
    loop.run_until_complete(download_manager(url, num_chunks))

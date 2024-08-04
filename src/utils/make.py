import aiofiles, logging, os

import aiofiles.os


async def make_dir(path: str) -> None:
    await aiofiles.os.makedirs(path, exist_ok=True)
    logging.info(f"Make dir: {path}")


async def remove_file(path: str) -> None:
    if os.path.exists(path):
        await aiofiles.os.remove(path)
        logging.info(f"Remove file: {path}")

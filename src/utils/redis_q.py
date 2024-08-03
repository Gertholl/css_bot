import os

from aiogram import Bot, types
from rq import Queue
from config import Settings


async def create_task(
    chat_id: int, bot: Bot, config: Settings, q: Queue, document: types.Document
):
    upload_user_path = os.path.join(
        config.UPLOAD_DIR,
        str(chat_id),
    )

    result_user_path = os.path.join(
        config.RESULT_FOLDER,
        str(chat_id),
    )

import os, aiofiles
import aiofiles.os
from aiogram import types, F, Router, Bot
from rq import Queue
from config import Settings
from src.keybords.inline_keybords import inline_kb
from src.utils.make import make_dir
import worker


message_router = Router()


@message_router.message(F.document)
async def process_document(
    message: types.Message,
    bot: Bot,
    config: Settings,
    q: Queue,
):
    document = message.document

    if (
        document.mime_type != "text/comma-separated-values"
        and document.mime_type != "text/csv"
    ):
        await message.reply("Это не CSV файл")
        return

    upload_user_path = os.path.join(
        config.UPLOAD_DIR,
        str(message.chat.id),
    )

    result_user_path = os.path.join(
        config.RESULT_FOLDER,
        str(message.chat.id),
    )

    file_info = await bot.get_file(file_id=document.file_id)

    upload_path = os.path.join(upload_user_path, str(document.file_name))
    result_path = os.path.join(
        result_user_path,
        str(document.file_name),
    )

    await make_dir(upload_user_path)
    await make_dir(result_user_path)

    if os.path.exists(upload_path):

        await message.reply(
            "Файл с таким именем уже существует", reply_markup=inline_kb(document)
        )
        return

    msg = await bot.send_message(message.chat.id, "Скачиваю файл...")
    await bot.download_file(file_path=file_info.file_path, destination=upload_path)

    job = q.enqueue(
        worker.process_file,
        args=(
            upload_path,
            result_path,
            message.chat.id,
            msg.message_id,
            config.API_TOKEN,
            config.REDIS_URL,
        ),
    )
    msg = await msg.edit_text(
        "Файл добавлен в очередь на обработку. ID задачи: " + job.id
    )

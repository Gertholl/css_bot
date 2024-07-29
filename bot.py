import argparse
import asyncio
from enum import Enum
import json
from venv import logger
from aiogram.webhook.aiohttp_server import SimpleRequestHandler, setup_application
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.filters.callback_data import CallbackData
import logging
import os
from aiogram import Bot, Dispatcher, Router, types
from aiogram.filters import Command
from aiogram.types import FSInputFile, BotCommand, BotCommandScopeDefault, Update
from aiohttp import web
from aiogram import F
from redis import Redis
from rq import Queue
from dotenv import load_dotenv

from config import Config


logging.basicConfig(level=logging.DEBUG)

load_dotenv(".env")
config = Config()

router = Router()
callback_router = Router()


class Action(str, Enum):
    DOWNLOAD = "download"
    PROCESS = "process"
    DELETE = "delete"


class FileExistsCallbackData(CallbackData, prefix="file_exists"):
    action: Action
    file_name: str


os.makedirs(config.UPLOAD_DIR, exist_ok=True)
os.makedirs(config.RESULT_FOLDER, exist_ok=True)

redis_conn = Redis.from_url(config.REDIS_URL)
q = Queue(connection=redis_conn)


@router.message(Command("start"))
@router.message(Command("help"))
async def send_welcome(message: types.Message):
    await message.reply("Привет, пришли мне CSV файл, и я обработаю его для тебя")


@router.message(F.document)
async def echo(message: types.Message, bot: Bot):

    document = message.document

    print(message, document, document.mime_type)

    if (
        document.mime_type != "text/comma-separated-values"
        and document.mime_type != "text/csv"
    ):
        await message.reply("Это не CSV файл")
        return

    file_info = await bot.get_file(file_id=document.file_id)
    upload_user_path = os.path.join(
        config.UPLOAD_DIR,
        str(message.chat.id),
    )

    result_user_path = os.path.join(
        config.RESULT_FOLDER,
        str(message.chat.id),
    )

    os.makedirs(upload_user_path, exist_ok=True)
    os.makedirs(result_user_path, exist_ok=True)

    upload_path = os.path.join(
        upload_user_path,
        document.file_name,
    )
    result_path = os.path.join(
        result_user_path,
        document.file_name,
    )

    if os.path.exists(upload_path):

        # Создаем инлайн кнопки
        builder = InlineKeyboardBuilder()

        # Добавляем кнопки в клавиатуру
        builder.row(
            InlineKeyboardButton(
                text="Скачать",
                callback_data=FileExistsCallbackData(
                    action=Action.DOWNLOAD, file_name=document.file_name
                ).pack(),
            ),
            InlineKeyboardButton(
                text="Обработать",
                callback_data=FileExistsCallbackData(
                    action=Action.PROCESS, file_name=document.file_name
                ).pack(),
            ),
            InlineKeyboardButton(
                text="Удалить",
                callback_data=FileExistsCallbackData(
                    action=Action.DELETE, file_name=document.file_name
                ).pack(),
            ),
            width=3,
        )

        await message.reply(
            "Файл с таким именем уже существует", reply_markup=builder.as_markup()
        )
        return

    msg = await bot.send_message(message.chat.id, "Скачиваю файл...")
    await bot.download_file(file_path=file_info.file_path, destination=upload_path)

    job = q.enqueue(
        "worker.process_file",
        args=(
            upload_path,
            result_path,
            message.chat.id,
            msg.message_id,
        ),
    )
    msg = await msg.edit_text(
        "Файл добавлен в очередь на обработку. ID задачи: " + job.id
    )


async def on_startup(bot: Bot):
    logging.info("Bot started")
    await bot.delete_webhook()
    await bot.set_webhook(
        url=f"{config.WEBHOOK_HOST}/webhook/{config.API_TOKEN}",
        drop_pending_updates=True,
        secret_token=config.SECRET_TOKEN,
        allowed_updates=["message", "callback_query"],
    )
    data = await bot.get_webhook_info()
    logging.info(data.dict())


async def on_shutdown(bot: Bot):
    await bot.delete_webhook()


async def health_check(request: web.Request):
    hook = await request.app["bot"].get_webhook_info()
    logging.info(f"Health check: {hook.dict()}")
    return web.json_response(data={"status": "ok"})


@callback_router.callback_query(
    FileExistsCallbackData.filter(F.action == Action.DOWNLOAD)
)
async def download(
    query: types.CallbackQuery, callback_data: FileExistsCallbackData, bot: Bot
):
    await query.answer()
    f_name = callback_data.file_name
    upload = os.path.join(config.UPLOAD_DIR, str(query.message.chat.id), f_name)
    result = os.path.join(config.RESULT_FOLDER, str(query.message.chat.id), f_name)
    logging.info("Download callback")
    await query.message.reply_document(
        document=FSInputFile(upload),
        caption="Данный файл еще не обработан",
        reply_markup=InlineKeyboardMarkup(
            inline_keyboard=[
                [
                    InlineKeyboardButton(
                        text="Обработать",
                        callback_data=FileExistsCallbackData(
                            action=Action.PROCESS, file_name=f_name
                        ).pack(),
                    ),
                    InlineKeyboardButton(
                        text="Удалить",
                        callback_data=FileExistsCallbackData(
                            action=Action.DELETE, file_name=f_name
                        ).pack(),
                    ),
                ]
            ]
        ),
    )


@callback_router.callback_query(
    FileExistsCallbackData.filter(F.action == Action.PROCESS)
)
async def process(
    query: types.CallbackQuery, callback_data: FileExistsCallbackData, bot: Bot
):
    await query.answer()
    logging.info("Process callback")
    f_name = callback_data.file_name
    upload = os.path.join(config.UPLOAD_DIR, str(query.message.chat.id), f_name)
    result = os.path.join(config.RESULT_FOLDER, str(query.message.chat.id), f_name)
    msg = await query.message.answer(
        text="Валидация данных. Это может занять некоторое время",
    )
    job = q.enqueue(
        "worker.process_file",
        args=(
            upload,
            result,
            str(query.message.chat.id),
            msg.message_id,
        ),
    )
    await query.message.delete()

    msg = await msg.edit_text(
        text="Файл добавлен в очередь. ID: {}".format(job.id),
    )


@callback_router.callback_query(
    FileExistsCallbackData.filter(F.action == Action.DELETE)
)
async def process(
    query: types.CallbackQuery, callback_data: FileExistsCallbackData, bot: Bot
):
    await query.answer()
    logging.info("Delete callback")
    f_name = callback_data.file_name
    upload = os.path.join(config.UPLOAD_DIR, str(query.message.chat.id), f_name)
    result = os.path.join(config.RESULT_FOLDER, str(query.message.chat.id), f_name)
    os.remove(upload)
    await query.message.delete()
    await query.answer("Файл удален c cервера")


def main():

    dp = Dispatcher()
    dp.include_router(router)
    dp.include_router(callback_router)
    dp.startup.register(on_startup)
    dp.shutdown.register(on_shutdown)

    bot = Bot(token=config.API_TOKEN)

    app = web.Application()
    app["bot"] = bot
    app.router.add_get("/health_check", health_check)

    webhook_requests_handler = SimpleRequestHandler(
        dispatcher=dp,
        bot=bot,
        secret_token=config.SECRET_TOKEN,
    )
    webhook_requests_handler.register(app, path=f"/webhook/{config.API_TOKEN}")
    setup_application(app, dp, bot=bot)

    web.run_app(app, host=config.WEBSERVER_HOST, port=config.WEBSERVER_PORT)


if __name__ == "__main__":
    asyncio.run(main())

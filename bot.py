import asyncio
from enum import Enum
from typing import Literal
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
import click
from redis import Redis
from rq import Queue
from dotenv import load_dotenv

from config import Settings
from src.utils.make import make_dir
from src.handlers.message import message_router
from src.handlers.command import command_router
from src.handlers.callback import callback_router


logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)


async def on_startup(bot: Bot, config: Settings):
    logging.info("Bot started")
    await make_dir(config.UPLOAD_DIR)
    await make_dir(config.RESULT_FOLDER)
    await bot.delete_webhook()
    logging.info(f"{config.MODE=}")
    if config.MODE == "dev":
        await bot.set_webhook(
            url=f"{config.WEBHOOK_HOST}/webhook/{config.API_TOKEN}",
            drop_pending_updates=True,
            secret_token=config.SECRET_TOKEN,
            allowed_updates=["message", "callback_query"],
        )
    else:
        await bot.set_webhook(
            url=f"{config.WEBHOOK_HOST}/webhook/{config.API_TOKEN}",
            drop_pending_updates=True,
            secret_token=config.SECRET_TOKEN,
            certificate=FSInputFile("./certs/server_cert.pem"),
            allowed_updates=["message", "callback_query"],
        )
    data = await bot.get_webhook_info()
    await bot.send_message(chat_id=239643021, text="Bot started")
    logging.info(data.dict())


async def on_shutdown(bot: Bot):
    await bot.delete_webhook()


async def health_check(request: web.Request):
    hook = await request.app["bot"].get_webhook_info()
    logging.info(f"Health check: {hook.dict()}")
    return web.json_response(data={"status": "ok"})


@click.command()
@click.option("--mode", default="dev", help='The mode. Default: "dev"')
@click.option(
    "--host", default="127.0.0.1", help='The host addres. Default: "127.0.0.1"'
)
@click.option("--port", default=8000, help="The port. Default: 8000")
@click.option("--token", help="The bot token")
@click.option("--secret", help="The secret token")
@click.option("--redis_url", help="The redis url")
@click.option("--webhook_host", help="The webhook host")
@click.option("--webhook_port", help="The webhook port")
@click.option("--webhook_path", help="The webhook path")
@click.option("--upload_dir", help="The upload dir")
@click.option("--result_folder", help="The result folder")
def main(
    host,
    port,
    token,
    secret,
    redis_url,
    webhook_host,
    webhook_port,
    webhook_path,
    upload_dir,
    result_folder,
    mode: Literal["dev", "prod"],
):
    if mode == "dev":
        logging.basicConfig(level=logging.DEBUG)
    elif mode == "prod":
        logging.basicConfig(level=logging.INFO)

    config = Settings(
        API_TOKEN=token,
        SECRET_TOKEN=secret,
        REDIS_URL=redis_url,
        WEBHOOK_HOST=webhook_host,
        WEBHOOK_PORT=webhook_port,
        WEBHOOK_PATH=webhook_path,
        UPLOAD_DIR=upload_dir,
        RESULT_FOLDER=result_folder,
        WEBSERVER_HOST=host,
        WEBSERVER_PORT=port,
        MODE=mode,
    )

    redis_conn = Redis.from_url(config.REDIS_URL)
    q = Queue(connection=redis_conn)
    dp = Dispatcher(config=config, q=q)
    dp.include_router(command_router)
    dp.include_router(message_router)
    dp.include_router(callback_router)
    dp.startup.register(on_startup)
    dp.shutdown.register(on_shutdown)
    bot = Bot(token=config.API_TOKEN)
    app = web.Application()
    app["bot"] = bot
    app["config"] = config
    app["queue"] = q
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

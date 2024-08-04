from aiogram import Router
from aiogram.filters import Command
from aiogram import F, types, Bot
from config import Settings
import os


command_router = Router()


@command_router.message(Command("start"))
@command_router.message(Command("help"))
async def send_welcome(message: types.Message, bot: Bot, config: Settings):
    await message.reply("Привет, пришли мне CSV файл, и я обработаю его для тебя")

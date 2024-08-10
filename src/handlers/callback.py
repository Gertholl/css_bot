from aiogram import Router, Bot, F, types
from rq import Queue
from src.common.enums import Action
from config import Settings
from src.filters.callback_data import FileExistsCallbackData

import os, logging


callback_router = Router()


@callback_router.callback_query(
    FileExistsCallbackData.filter(F.action == Action.DOWNLOAD)
)
async def download(
    query: types.CallbackQuery,
    callback_data: FileExistsCallbackData,
    bot: Bot,
    q: Queue,
    config: Settings,
):
    await query.answer()
    f_name = callback_data.file_name
    upload = os.path.join(config.UPLOAD_DIR, str(query.message.chat.id), f_name)
    result = os.path.join(config.RESULT_FOLDER, str(query.message.chat.id), f_name)
    logging.info("Download callback")
    await query.message.reply_document(
        document=types.FSInputFile(upload),
        caption="Данный файл еще не обработан",
        reply_markup=types.InlineKeyboardMarkup(
            inline_keyboard=[
                [
                    types.InlineKeyboardButton(
                        text="Обработать",
                        callback_data=FileExistsCallbackData(
                            action=Action.PROCESS, file_name=f_name
                        ).pack(),
                    ),
                    types.InlineKeyboardButton(
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
    query: types.CallbackQuery,
    callback_data: FileExistsCallbackData,
    bot: Bot,
    q: Queue,
    config: Settings,
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
            config.API_TOKEN,
            config.REDIS_URL,
        ),
    )
    await query.message.delete()

    msg = await msg.edit_text(
        text="Файл добавлен в очередь. ID: {}".format(job.id),
    )


@callback_router.callback_query(
    FileExistsCallbackData.filter(F.action == Action.DELETE)
)
async def process_delete(
    query: types.CallbackQuery,
    callback_data: FileExistsCallbackData,
    bot: Bot,
    q: Queue,
    config: Settings,
):
    await query.answer()
    logging.info("Delete callback")
    f_name = callback_data.file_name
    upload = os.path.join(config.UPLOAD_DIR, str(query.message.chat.id), f_name)
    result = os.path.join(config.RESULT_FOLDER, str(query.message.chat.id), f_name)
    os.remove(upload)
    await query.message.delete()
    await query.answer("Файл удален c cервера")

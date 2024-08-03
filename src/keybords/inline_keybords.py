from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, Document
from aiogram.utils.keyboard import InlineKeyboardBuilder
from src.filters.callback_data import FileExistsCallbackData
from src.common.enums import Action


def inline_kb(document: Document) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    file_name = str(document.file_name)
    # Добавляем кнопки в клавиатуру
    builder.row(
        InlineKeyboardButton(
            text="Скачать",
            callback_data=FileExistsCallbackData(
                action=Action.DOWNLOAD, file_name=file_name
            ).pack(),
        ),
        InlineKeyboardButton(
            text="Обработать",
            callback_data=FileExistsCallbackData(
                action=Action.PROCESS, file_name=file_name
            ).pack(),
        ),
        InlineKeyboardButton(
            text="Удалить",
            callback_data=FileExistsCallbackData(
                action=Action.DELETE, file_name=file_name
            ).pack(),
        ),
        width=3,
    )

    return builder.as_markup()

from src.common.enums import Action
from aiogram.filters.callback_data import CallbackData


class FileExistsCallbackData(CallbackData, prefix="file_exists"):
    action: Action
    file_name: str

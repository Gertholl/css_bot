import pandas as pd
from redis import Redis
from rq import Queue
import re
import os
from aiogram.types import FSInputFile
from aiogram import Bot, types

import logging


url_pattern = re.compile(r"https?://[^\s/$.?#].[^\s]*")
size_pattern = re.compile(r"\d+/\d+")


def parse_characteristics(char_str):
    characteristics = {}
    if isinstance(char_str, str):
        # Поиск ссылки в строке
        found_urls = url_pattern.findall(char_str)
        found_urls = [u.replace(",", "") for u in found_urls]

        if found_urls:
            # Удаление повторяющихся ссылок
            filter_urls = []
            for u in found_urls:
                char_str = char_str.replace(u, "").strip()

                if ".jpg" in u:
                    filter_urls.append(u)
                elif ".png" in u:
                    filter_urls.append(u)
                elif ".jpeg" in u:
                    filter_urls.append(u)
                else:
                    continue

            urls = ",".join(filter_urls)
            # Удаление найденной ссылки из строки
            characteristics["Image_url"] = urls
        else:
            characteristics["Image_url"] = None

        # Разбиваем оставшуюся строку по '/'
        items = char_str.split("/ ")

        # Обрабатываем оставшиеся элементы
        for item in items:
            key_value = item.split(":", 1)
            if len(key_value) == 2:
                key = key_value[0].strip()
                value = key_value[1].strip()
                if not re.findall(size_pattern, value):
                    value = value.replace("/", "")
                characteristics[key] = value
    return characteristics


def parse_exclusive(char_str):
    characteristics = {}
    if isinstance(char_str, str):
        items = char_str.split(" - ")

        characteristics["Эксклюзив"] = items[1]

    return characteristics


def parse_category(char_str):
    characteristics = {}
    if isinstance(char_str, str):
        items = char_str.split(" - ")

        characteristics["Категория"] = items[0]
        characteristics["Подкатегория"] = items[1]

    return characteristics


def parse_price(char_str):
    characteristics = {}
    if isinstance(char_str, str):
        items = char_str.split(" ")

        characteristics["Цена"] = items[0]
        if items[1] == "руб.":
            characteristics["Валюта"] = "RUB"
    return characteristics


def process_file(file_path, result_path, chat_id, message_id, bot_token, redis_url):
    # Загрузка CSV файла
    try:
        print(file_path, result_path)
        logging.info(f"Processing file: {file_path}")
        logging.debug(f"{bot_token}, {redis_url}")
        bot = Bot(token=bot_token)
        q = Queue(connection=Redis.from_url(redis_url))
        df = pd.read_csv(file_path, delimiter=";", header=0)

        # Получение 4-й колонки
        col4_data = df['Характеристики']
        col16_data = df['Эксклюзив']
        col3_data = df['Название категории']
        col14_data = df['Цена']

        # Регулярное выражение для поиска ссылки

        # Функция для разбора строки и извлечения данных

        # Применение функции к данным из 4-й колонки
        parsed_data = col4_data.apply(parse_characteristics)
        parsed_df = pd.json_normalize(parsed_data)

        parsed16_col = col16_data.apply(parse_exclusive)
        parsed_16_col_df = pd.json_normalize(parsed16_col)

        parsed3_col = col3_data.apply(parse_category)
        parsed_3_col_df = pd.json_normalize(parsed3_col)

        parsed14_col = col14_data.apply(parse_price)
        parsed_14_col_df = pd.json_normalize(parsed14_col)

        # Удаление 4-й колонки из исходного DataFrame
        df.drop(columns=["Характеристики", "Название категории", "Эксклюзив", "Цена"], inplace=True)

        df.rename(
            columns={
                0: "Продукт",
                14: "Цена",
                2: "Производитель",
                15: "Артикул",
                8: "Описание",
            },
            inplace=True,
        )

        # Объединение исходного DataFrame с новым DataFrame
        result_df = pd.concat(
            [df, parsed_3_col_df, parsed_14_col_df, parsed_16_col_df, parsed_df], axis=1
        )

        # Удаление пустых колонок
        result_df.dropna(axis=1, how="all", inplace=True)
        # Сохранение результата в новый CSV файл
        result_df.to_csv(
            result_path,
            sep=";",
            index=False,
            mode="w",
            encoding="utf-8",
        )

        q.enqueue(
            send_result,
            args=(result_path, file_path, chat_id, message_id, bot_token),
        )

        return result_path
    except Exception as e:
        q.enqueue(
            send_error,
            args=(result_path, file_path, chat_id, message_id, bot_token),
        )


async def send_error(result_path, upload_path, chat_id, message_id, bot_token):
    bot = Bot(token=bot_token)
    await bot.delete_messages(chat_id=chat_id, message_ids=[message_id])
    await bot.send_message(
        chat_id=chat_id,
        text="Произошла ошибка при обработке. Пожалуйста, повторите попытку позже.",
    )
    os.remove(upload_path)


async def send_result(result_path, upload_path, chat_id, message_id, bot_token):
    bot = Bot(token=bot_token)
    await bot.delete_messages(chat_id=chat_id, message_ids=[message_id])
    await bot.send_document(
        chat_id=chat_id,
        document=FSInputFile(result_path),
        caption="Результат обработки",
    )
    os.remove(upload_path)
    os.remove(result_path)

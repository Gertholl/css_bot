import pandas as pd
import re


df = pd.read_csv("Расширительные баки.csv", delimiter=";")

col4 = df.iloc[:, 4]
url_pattern = re.compile(r"https?://[^\s/$.?#].[^\s]*")


def parse_characteristics(char_str):
    characteristics = {}

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

    for i in items:
        if ":" in i:
            key, value = i.split(":")
            characteristics[key.strip()] = value.strip()
    print(characteristics)
    return characteristics


data = col4.apply(parse_characteristics)
print(data)

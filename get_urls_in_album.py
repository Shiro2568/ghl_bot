import re
import requests

# Функция getPlaylistLinks принимает URL плейлиста и возвращает набор ссылок на видео.
def getPlaylistLinks(url: str) -> set:
    # Получаем текстовое содержимое страницы по указанному URL.
    page_text = requests.get(url).text

    # Создаем регулярное выражение для поиска ссылок на видео в плейлисте.
    parser = re.compile(r"watch\?v=\S+?list=")
    # Ищем все совпадения регулярного выражения в тексте страницы.
    playlist = set(re.findall(parser, page_text))
    # Преобразуем найденные ссылки в уникальный набор.
    # Преобразуем каждую ссылку, добавляем префикс и убираем ненужные символы.
    playlist = map(
        (lambda x: "https://www.youtube.com/" + x.replace("\\u0026list=", "")), playlist
    )
    return playlist
#print(requests.get("https://www.youtube.com/watch?v=W87wOCSPA08&list=RDEMp8p5zGq5BXS6mk53kXuvbg&index=3").text)
# Если этот файл запускается как основной скрипт (а не импортируется из другого файла),
# то выполняется следующий код:
if __name__ == "__main__":
    urls = []
    # Указываем URL плейлиста для обработки.
    url = "https://www.youtube.com/watch?v=cdX8r3ZSzN4&list=RDEMp8p5zGq5BXS6mk53kXuvbg&start_radio=1"

    # Получаем набор ссылок на видео.
    output = getPlaylistLinks(url)
    print(output)
    # Инициализируем счетчик для нумерации ссылок.
    index = 1
    # Печатаем каждую ссылку с ее номером.
    for link in output:
        urls.append(link)
        index += 1 
    if not urls:
        print("Это не альбом")
    else:
        print("Альбом")
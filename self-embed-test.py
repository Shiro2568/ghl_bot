import requests
url = 'https://discord.com/api/v9/channels/1106606903519350927/messages'

headers = {
    'Authorization': 'NDU3MTAwNTg4OTcxMTk2NDE3.GvVszi.mXeLyvjFbbo9ycKoHLBIatd2XKfHo-EzWN4U-Y',
    'Content-Type': 'application/json'
}

data = {
    "content": "Bruh",  # Добавьте небольшой пробел как контент
    "embeds": [
        {
            "type": "rich",
            "title": "Успешно скипнуто!",
            "description": "Ты гавно!",
            "color": 0x00FFFF,
            "url": "https://i.ytimg.com/vi/2J8PlAttqZA/hqdefault.jpg"
        }
    ]
}



response = requests.post(url, headers=headers, json=data)

print(response.json())






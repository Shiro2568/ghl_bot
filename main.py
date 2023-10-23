import sys
sys.path.insert(0, 'discord.py-self')
sys.path.insert(0, 'discord.py-self_embed')

import secrets
import re
import asyncio
import requests
import discord
from discord.ext import commands
#import discord_self_embed - не работает
import json
import youtube_dl
import time
import random
import os



yt_dl_opts = {'format': 'bestaudio/best'}  # Опции для youtube_dl

ffmpeg_options = {
    'options': '-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5',  # Параметры для FFmpeg
    'before_options': '-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5',  # Параметры перед началом воспроизведения
}
voice_clients = {}

queue = []
#Если пользователь захотел залупить очередь
looped = False

# Инициализируем youtube_dl
ytdl = youtube_dl.YoutubeDL(yt_dl_opts)  # Создаем объект youtube_dl с нашими опциями

#temp_token = secrets.token_hex(16)
last_video_queue = None
with open('config.json', 'r') as file:
    config = json.load(file)
  
token = config['token']
prefix = config['prefix']
index_loop = 0
bot = commands.Bot(command_prefix=prefix, self_bot=True)
user_roles = []
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

async def go_extract(url):
    return await asyncio.gather(extract_video_info(url))  
 
async def extract_video_info(url):
    data = await bot.loop.run_in_executor(None, lambda: ytdl.extract_info(url, download=False))
    return data
@bot.command()
async def ping(ctx):
    await bot.change_presence(activity=discord.Game(name="Your Status Here"))

@bot.event
async def on_message(mess):
    global queue,looped,user_message,lst_serv,playing,index_loop,last_video_queue, next_play,cur_sng_name  # Разрешаем изменение глобальной переменной queue
    msg = mess
    if msg.content.startswith("??"):
        for role in msg.author.roles:
            user_roles.append(role.id)
        if 1164549067704111174 in user_roles:
            if msg.content.startswith('??queue_size'):
                if queue:
                    if last_video_queue and not next_play:
                        data = last_video_queue
                    else:
                        data = await bot.loop.run_in_executor(None, lambda: ytdl.extract_info(queue[-1], download=False))
                        last_video_queue = data
                        next_play = False
                    #data = await bot.loop.run_in_executor(None, lambda: ytdl.extract_info(queue[-1], download=False))
                else:
                    if voice_clients[msg.guild.id].is_playing():
                        if last_video_queue and not next_play:
                            data = last_video_queue
                        else:
                            data = await bot.loop.run_in_executor(None, lambda: ytdl.extract_info(cur_url, download=False))
                            last_video_queue = data
                            next_play = False
                        #data = await bot.loop.run_in_executor(None, lambda: ytdl.extract_info(cur_url, download=False))
                song_thumbnail = data["thumbnail"]
                song_duration = data["duration"]
                song_title = data['title'];
                hours = song_duration // 3600
                minutes = (song_duration % 3600) // 60
                seconds = song_duration % 60
                if hours < 10:
                    hours = f"0{hours}"
                if minutes < 10:
                    minutes = f"0{minutes}"
                if seconds < 10:
                    seconds = f"0{seconds}"
                response = requests.get(song_thumbnail)
                with open("last_thumbnail.jpg", "wb") as file:
                    file.write(response.content)
                    #embed.add_field(name="Field-1", value="duration", inline=False)
                await msg.author.send(f"Последняя песня в очереди: {song_title} ({hours}:{minutes}:{seconds})\nКоличество песен в очереди: {len(queue)}",file=discord.File("last_thumbnail.jpg"));

            #Логика снятие лупа.
            if msg.content.startswith('??loop'):
                if looped:
                    looped = False
                    index_loop = 0
                    await msg.author.send("Отлупил текущую песню.")
                else:
                    looped = True
                    await msg.author.send("Залупил текущую песню.")
            if msg.content.startswith('??skip-all'):
                if looped:
                    queue = []
                    index_loop = 0
                    voice_clients[msg.guild.id].stop()
                    await msg.author.send(f"\nУспешно скипнул всю очередь! Добавьте новые песни в залупленную очередь!")
                else:
                    queue = []
                    voice_clients[msg.guild.id].stop()
                    await msg.author.send(f"\nУспешно скипнул всю очередь! Добавьте новые песни в очередь")

            if msg.content.startswith('??skip'):
                if looped:
                    if index_loop == len(queue):
                        index_loop = 0
                        if len(queue) == 0:
                            await msg.author.send(f"\nНельзя скипнуть трек, если он один в залупенной очереди.")
                        else:
                            voice_clients[msg.guild.id].stop()
                    else: 
                        index_loop += 1 
                        voice_clients[msg.guild.id].stop()
                        await msg.author.send(f"\nУспешно скипнул залупленый трек! Включаю следующий")
                    loop(msg.guild.id,index_loop,msg)
                else:
                    if msg.content.startswith('??skip') and len(queue) == 0:
                        try:
                            if voice_clients[msg.guild.id].is_playing():
                                voice_clients[msg.guild.id].stop()
                                await msg.author.send(f"\nУспешно скипнуто")
                                await msg.author.send(f"\nМузыки больше нету, добавьте её в очередь.")
                        except Exception as err:
                            await msg.author.send(f"\nНечего скипать.")
                                
                    elif msg.content.startswith('??skip') and len(queue) != 0:
                        voice_clients[msg.guild.id].stop()
                        data = await bot.loop.run_in_executor(None, lambda: ytdl.extract_info(queue[-1], download=False, extra_info={'verbose': 'True'}))
                        song_name = data['title']
                        song_duration = data['duration']
                        song_thumbnail = data['thumbnail']
                        response = requests.get(song_thumbnail)
                        with open("thumbnail.jpg", "wb") as file:
                            file.write(response.content)
                        #embed.add_field(name="Field-1", value="duration", inline=False)
                        await msg.author.send(content=f"Успешно скипнуто! Следующий трек - {song_name}",file=discord.File("thumbnail.jpg"))
                        os.remove("thumbnail.jpg")
                # Если музыка не играет, запускаем следующий трек
                if not voice_clients[msg.guild.id].is_playing() and not looped:
                    await play_next(msg.guild.id,msg)
                if not voice_clients[msg.guild.id].is_playing() and looped:
                    await loop(msg.guild.id,0,msg)
            # Проверяем, начинается ли сообщение с '??play'
            if msg.content.startswith('??play'):
                next_play = True
                lst_serv = msg.guild.id
                try:
                    # Получаем URL из сообщения
                    url = msg.content.split()[1]
                    try:
                        if url.split("&")[1]:
                            output = getPlaylistLinks(url)
                            urls = []
                            for link in output:
                                urls.append(link) 
                            queue.extend(urls)
                            await msg.author.send(f"{url}\nАльбом успешно был добавлен в очередь. Количество песен в очереди: {len(queue)}")

                    except:
                            if url.split("?")[1]:
                                if url.split("?")[0] == 'https://www.youtube.com/playlist':
                                    output = getPlaylistLinks(url)
                                    urls = []
                                    for link in output:
                                        urls.append(link) 
                                    queue.extend(urls)
                                    await msg.author.send(f"{url}\nАльбом успешно был добавлен в очередь. Количество песен в очереди: {len(queue)}")
                                else:
                                    queue.append(url)
                                    await msg.author.send(f"{url}\nПесня успешно была добавлена в очередь.Количество песен в очереди: {len(queue)}")

                        
                            
                    

                    #await mess.delete()
                    # Проверяем, находится ли бот в голосовом канале
                    if msg.guild.id not in voice_clients:
                        # Если нет, присоединяемся к голосовому каналу автора сообщения
                        print(msg.author.voice.channel)
                        voice_client = await msg.author.voice.channel.connect()
                        voice_clients[msg.guild.id] = voice_client  # Записываем клиент голосового канала в словарь
                        #queue.append(url)
                    # Добавляем URL в очередь
                    
                    
                    else:
                        pass
                        #queue.append(url)
                    
                    
                    # Если музыка не играет, запускаем следующий трек
                    if not voice_clients[msg.guild.id].is_playing() and not looped:
                        await play_next(msg.guild.id,msg)
                    if not voice_clients[msg.guild.id].is_playing() and looped:
                        await loop(msg.guild.id,0,msg)
                except Exception as err:
                    print(err)
            if msg.content.startswith("??stop"):
                if  voice_clients[msg.guild.id].is_playing():
                            voice_clients[msg.guild.id].pause()
                            print(voice_clients[msg.guild.id].pause())
                            print(voice_clients[msg.guild.id])
                            await bot.change_presence(status=discord.Status.online, activity=discord.Streaming(platform="Транслирует на YouTube", url= cur_url, name="YouTube",details="Трек на паузе.",assets={"small_image": "Kuro", "large_image": "Shiro"}))

            if msg.content.startswith("??start"):
                if not voice_clients[msg.guild.id].is_playing():
                    voice_clients[msg.guild.id].resume()
                    await bot.change_presence(status=discord.Status.online, activity=discord.Streaming(platform="Транслирует на YouTube", url= cur_url, name="YouTube",details=cur_sng_name,assets={"small_image": "Kuro", "large_image": "Shiro"}))

            if msg.content.startswith('??relocate'):
                if  voice_clients[msg.guild.id].is_playing():
                    playing = True
                else: 
                    playing = False
                # Проверяем, находится ли бот в голосовом канале. Так же проверяем что человек находится на том сервере что и бот.
                if msg.guild.id in voice_clients:
                    await voice_clients[msg.guild.id].disconnect()  # Отключаемся от голосового канала
                    voice_client = await msg.author.voice.channel.connect()
                    voice_clients[msg.guild.id] = voice_client  # Записываем клиент голосового канала в словарь
                    if playing:
                        play_next(msg.guild.id,msg)
                    # Если нет, присоединяемся к голосовому каналу автора сообщения
                else:
                    #Если человек находится на другом сервере, удаляем его клиент на последнем сервере, и добавляем новый сервер в клиент.
                    await voice_clients[lst_serv].disconnect()
                    del voice_clients[lst_serv]
                    voice_client = await msg.author.voice.channel.connect()
                    voice_clients[msg.guild.id] = voice_client  # Записываем клиент голосового канала в словарь

   

async def loop(guild_id,index,msg):
        global index_loop
        index_loop = index
        if not looped:
               await play_next(guild_id,msg)
        else:
            if len(queue) == 0:
                pass
            else:
                if index >= len(queue)-1:
                    data = await bot.loop.run_in_executor(None, lambda: ytdl.extract_info(queue[index], download=False, extra_info={'verbose': 'True'}))

                    song = data['url']  # Получаем URL трека

                    player = discord.FFmpegPCMAudio(song, **ffmpeg_options)
                    response = requests.get(data["thumbnail"])
                    with open("thumbnail.jpg", "wb") as file:
                        file.write(response.content)
                    await msg.author.send(content=f"Запускаю текущий трек - {data['title']}",file=discord.File("thumbnail.jpg"))
                    os.remove("thumbnail.jpg")
                    # Проигрываем аудио в голосовом канале, после окончания запускаем следующий трек
                    await bot.change_presence(status=discord.Status.online, activity=discord.Streaming(platform="Транслирует на YouTube", url= queue[index], name="YouTube",details=data['title'],assets={"small_image": "Kuro", "large_image": "Shiro"}))

                    voice_clients[guild_id].play(player, after=lambda e: bot.loop.create_task(loop(guild_id,0,msg)))
                    
                else:
                    data = await bot.loop.run_in_executor(None, lambda: ytdl.extract_info(queue[index], download=False, extra_info={'verbose': 'True'}))
                    song = data['url']  # Получаем URL трека
                    player = discord.FFmpegPCMAudio(song, **ffmpeg_options)
                    await bot.change_presence(status=discord.Status.online, activity=discord.Streaming(platform="Транслирует на YouTube", url= queue[index], name="YouTube",details=data['title'],assets={"small_image": "Kuro", "large_image": "Shiro"}))
                    response = requests.get(data["thumbnail"])
                    with open("thumbnail.jpg", "wb") as file:
                        file.write(response.content)
                    await msg.author.send(content=f"Запускаю текущий трек - {data['title']}",file=discord.File("thumbnail.jpg"))
                    os.remove("thumbnail.jpg")

                    # Проигрываем аудио в голосовом канале, после окончания запускаем следующий трек
                    voice_clients[guild_id].play(player, after=lambda e: bot.loop.create_task(loop(guild_id,index+1,msg)))

# Функция для воспроизведения следующего трека
async def play_next(guild_id,msg):
    global url, cur_url, last_video_queue,cur_sng_name
    if queue:  # Проверяем, есть ли что-то в очереди
        url = queue.pop(0)  # Извлекаем первый URL из очереди
        if looped:
            queue.append(cur_url)
            queue.append(url)
            print('test1')   
            await loop(guild_id,0,msg)
        else:
            cur_url = url
            # Используем youtube_dl для извлечения информации о треке
            await bot.change_presence(status=discord.Status.online, activity=discord.Streaming(platform="Транслирует на YouTube", url= cur_url, name="YouTube",details="Запуск трека, ожидайте.",assets={"small_image": "Kuro", "large_image": "Shiro"}))
            data = await bot.loop.run_in_executor(None, lambda: ytdl.extract_info(url, download=False, extra_info={'verbose': 'True'}))
            if last_video_queue:
                if last_video_queue['title'] == data['title']:
                    last_video_queue = data
                else:
                    last_video_queue = None
            song = data['url']  # Получаем URL трека
            
            song_name = data['title']
            cur_sng_name = song_name
            song_thumbnail = data['thumbnail']
            song_duration = data["duration"]
            print(song_name)
            hours = song_duration // 3600
            minutes = (song_duration % 3600) // 60
            seconds = song_duration % 60
            if hours < 10:
                hours = f"0{hours}"
            if minutes < 10:
                minutes = f"0{minutes}"
            if seconds < 10:
                seconds = f"0{seconds}"
            await bot.change_presence(status=discord.Status.online, activity=discord.Streaming(platform="Транслирует на YouTube", url= cur_url, name="YouTube",details=song_name,assets={"small_image": "Kuro", "large_image": "Shiro"}))
            #requests.patch("https://discord.com/api/v9/users/@me/settings", headers={"authorization": "NDU3MTAwNTg4OTcxMTk2NDE3.GvVszi.mXeLyvjFbbo9ycKoHLBIatd2XKfHo-EzWN4U-Y","content-type": "application/json"}, data=json.dumps({"custom_status":{"text":f"     Сейчас играет:      {song_name} | {hours}:{minutes}:{seconds}"}}))
            #await bot.change_presence(activity=discord.Game(f"Сейчас играет - {song_name}"))
            # Создаем аудио-плеер с использованием FFmpeg
            player = discord.FFmpegPCMAudio(song, **ffmpeg_options)

            # Проигрываем аудио в голосовом канале, после окончания запускаем следующий трек
            voice_clients[guild_id].play(player, after=lambda e: bot.loop.create_task(play_next(guild_id,msg)))
            await msg.author.send(f"\nЗапускаю следующий трек.")
        
    else:
        if looped:
            queue.append(url)  
            print('test2')
            await loop(guild_id,0,msg)
        else:
            await bot.change_presence(status=discord.Status.online, activity=discord.Streaming(platform="Транслирует на YouTube", url= 'https://www.youtube.com/', name="YouTube",details="Сейчас ничего не играет.",assets={"small_image": "Kuro", "large_image": "Shiro"}))
            await msg.author.send(f"\nПесня успешно закончилась, в очереди больше не осталось песен, добавьте новые песни в очередь.")
    


bot.run(token)
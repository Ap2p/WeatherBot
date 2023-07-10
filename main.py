import os
import datetime
import httpx
from aiogram import Bot, types
from aiogram.dispatcher import Dispatcher
from aiogram.types import ParseMode
from aiogram.utils import executor
from config import *
import math

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher(bot)


@dp.message_handler(commands=['start'])
async def start_command(msg: types.Message):
    await msg.reply('Привет! Напиши мне название города, и я пришлю сводку погоды')


@dp.message_handler()
async def get_weather(msg: types.Message):
    try:
        response = httpx.get(
            f'http://api.openweathermap.org/data/2.5/weather?q={msg.text}&appid={API_KEY}&units=metric')  # Исправлено на API_KEY
        data = response.json()
        city = data['name']
        cur_weather = data['main']['temp']
        humidity = data['main']['humidity']
        pressure = data['main']['pressure']
        wind = data['wind']['speed']

        sunrise_timestamp = datetime.datetime.fromtimestamp(data['sys']['sunrise'])
        sunset_timestamp = datetime.datetime.fromtimestamp(data['sys']['sunset'])

        length_day = sunset_timestamp - sunrise_timestamp

        code_to_smile = {
            "Clear": "Ясно ☀️",
            "Clouds": "Облачно ☁️",
            "Rain": "Дождь 🌧️",
            "Drizzle": "Дождь 🌧️",
            "Thunderstorm": "Гроза ⛈️",
            "Snow": "Снег 🌨️",
            "Mist": "Туман 🌫️"
        }

        weather_description = data['weather'][0]['main']

        if weather_description in code_to_smile:
            wd = code_to_smile[weather_description]
        else:
            wd = 'Посмотри в окно, я не понимаю, что там за погода...'

        await msg.reply(f"{datetime.datetime.now().strftime('%A %d-%b-%Y %H:%M')}\n"
                        f"Погода в городе: {city}\nТемпература: {cur_weather} °C - {wd}\n"
                        f"Влажность: {humidity}%\nДавление: {math.ceil(pressure / 1.333)} мм.рт.ст\nВетер: {wind} м/с \n"
                        f"Восход солнца: {sunrise_timestamp.strftime('%H:%M')}\nЗакат солнца: {sunset_timestamp.strftime('%H:%M')}\nПродолжительность дня: {length_day}\n"
                        f"Хорошего дня!", parse_mode=ParseMode.HTML)
    except Exception as e:  # Уточним тип ошибки для отладки
        print(f"An error occurred: {e}")
        await msg.reply('Проверьте название города')


if __name__ == '__main__':
    executor.start_polling(dp)

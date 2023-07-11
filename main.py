from datetime import datetime
from pytz import timezone
import httpx
from aiogram import Bot, Dispatcher, types
from aiogram.types import ParseMode
from aiogram.utils import executor
from config import *
from math import ceil

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher(bot)

# Функция для преобразования UTC времени в локальное время пользователя
def convert_utc_to_local(utc_time, tz):
    utc = datetime.strptime(utc_time, "%A %d-%b-%Y %H:%M:%S")
    local = utc.replace(tzinfo=timezone('UTC')).astimezone(timezone(tz))
    return local.strftime('%H:%M')

@dp.message_handler(commands=['start'])
async def start_command(msg: types.Message):
    await msg.reply('Привет! Напиши мне название города, и я пришлю сводку погоды')

@dp.message_handler()
async def get_weather(msg: types.Message):
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f'http://api.openweathermap.org/data/2.5/weather',
                params={'q': msg.text, 'appid': API_KEY, 'units': 'metric'}
            )
            response.raise_for_status()

            data = response.json()
            weather = data['weather'][0]
            main = data['main']
            wind = data['wind']
            sys = data['sys']

            city = data['name']
            cur_weather = main['temp']
            humidity = main['humidity']
            pressure = main['pressure']
            wind_speed = wind['speed']

            # Получаем текущую временную метку в UTC
            utc_time = datetime.utcnow().strftime('%A %d-%b-%Y %H:%M:%S')

            # Преобразуем временные метки в локальное время пользователя
            tz = msg.from_user.tzinfo  # Получаем часовой пояс пользователя
            sunrise_time = convert_utc_to_local(sys['sunrise'], tz)
            sunset_time = convert_utc_to_local(sys['sunset'], tz)

            # Вычисляем продолжительность дня
            length_day = datetime.strptime(sys['sunset'], "%%A %d-%b-%Y %H:%M:%S") - datetime.strptime(sys['sunrise'], "%A %d-%b-%Y %H:%M:%S")

            code_to_smile = {
                "Clear": "Ясно ☀️",
                "Clouds": "Облачно ☁️",
                "Rain": "Дождь 🌧️",
                "Drizzle": "Дождь 🌧️",
                "Thunderstorm": "Гроза ⛈️",
                "Snow": "Снег 🌨️",
                "Mist": "Туман 🌫️"
            }
            weather_description = code_to_smile.get(weather['main'], 'Посмотри в окно, я не понимаю, что там за погода...')

            await msg.reply(
                f"{datetime.now(tz).strftime('%A %d-%b-%Y %H:%M')}\n"  # Выводим текущую дату и время в локальное время пользователя
                f"Погода в городе: {city}\nТемпература: {cur_weather} °C - {weather_description}\n"
                f"Влажность: {humidity}%\nДавление: {ceil(pressure / 1.333)} мм.рт.ст\nВетер: {wind_speed} м/с \n"
                f"Восход солнца: {sunrise_time}\nЗакат солнца: {sunset_time}\nПродолжительность дня: {length_day}\n"
                f"Хорошего дня!",
                parse_mode=ParseMode.HTML
            )
    except httpx.HTTPError as http_err:
        print(f"HTTP error occurred: {http_err}")
        await msg.reply('Ошибка при выполнении HTTP-запроса')
    except Exception as e:
        print(f"An error occurred: {e}")
        await msg.reply('Произошла ошибка. Пожалуйста, попробуйте еще раз')

if __name__ == '__main__':
    executor.start_polling(dp)

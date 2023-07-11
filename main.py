from datetime import datetime

from pytz import timezone
import httpx
from aiogram import Bot, Dispatcher, types
from aiogram.types import ParseMode
from aiogram.utils import executor
from config import *
from math import ceil
from timezonefinder import TimezoneFinder


bot = Bot(token=BOT_TOKEN)
dp = Dispatcher(bot)

tf = TimezoneFinder()


async def get_city_timezone(lat, lon):
    tz_name = tf.timezone_at(lat=lat, lng=lon)
    if tz_name:
        return timezone(tz_name)

    return None


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
            coord = data['coord']

            city = data['name']
            cur_weather = main['temp']
            humidity = main['humidity']
            pressure = main['pressure']
            wind_speed = wind['speed']

            sunrise_timestamp = sys['sunrise']
            sunset_timestamp = sys['sunset']

            # Получаем информацию о временной зоне города
            city_timezone = await get_city_timezone(coord['lat'], coord['lon'])

            if city_timezone:
                # Преобразуем временные метки в локальное время города
                sunrise_time = datetime.fromtimestamp(sunrise_timestamp, timezone('UTC')).astimezone(city_timezone).strftime('%H:%M')
                sunset_time = datetime.fromtimestamp(sunset_timestamp, timezone('UTC')).astimezone(city_timezone).strftime('%H:%M')

                # Вычисляем продолжительность дня в часах и минутах
                length_day_seconds = sunset_timestamp - sunrise_timestamp
                length_day_hours = length_day_seconds // 3600
                length_day_minutes = (length_day_seconds % 3600) // 60

                code_to_smile = {
                    "Clear": "Ясно ☀️",
                    "Clouds": "Облачно ☁️",
                    "Rain": "Дождь 🌧️",
                    "Drizzle": "Дождь 🌧️",
                    "Thunderstorm": "Гроза ⛈️",
                    "Snow": "Снег 🌨️",
                    "Mist": "Туман 🌫️"
                }
                weather_description = code_to_smile.get(weather['main'],
                                                        'Посмотри в окно, я не понимаю, что там за погода...')

                await msg.reply(
                    f"{datetime.now(city_timezone).strftime('%A %d-%m-%Y %H:%M')}\n"
                    f"Погода в городе: {city}\nТемпература: {cur_weather} °C - {weather_description}\n"
                    f"Влажность: {humidity}%\nДавление: {ceil(pressure / 1.333)} мм.рт.ст\nВетер: {wind_speed} м/с \n"
                    f"Восход солнца: {sunrise_time}\nЗакат солнца: {sunset_time}\n"
                    f"Продолжительность дня: {length_day_hours} часов {length_day_minutes} минут\n"
                    f"Хорошего дня! 👋",
                    parse_mode=ParseMode.HTML
                )
            else:
                await msg.reply('Не удалось получить информацию о временной зоне для данного города.')
    except httpx.HTTPError as http_err:
        print(f"HTTP error occurred: {http_err}")
        await msg.reply('Ошибка при выполнении HTTP-запроса')
    except Exception as e:
        print(f"An error occurred: {e}")
        await msg.reply('Произошла ошибка. Пожалуйста, попробуйте еще раз')


if __name__ == '__main__':
    executor.start_polling(dp)

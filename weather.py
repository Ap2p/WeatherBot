from datetime import datetime
from pytz import timezone
from math import ceil
from timezonefinder import TimezoneFinder
import httpx

tf = TimezoneFinder()


async def get_city_timezone(lat, lon):
    tz_name = tf.timezone_at(lat=lat, lng=lon)
    if tz_name:
        return timezone(tz_name)

    return None


async def get_weather_data(city_name, api_key):
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f'http://api.openweathermap.org/data/2.5/weather',
                params={'q': city_name, 'appid': api_key, 'units': 'metric'}
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

                return {
                    'city': city,
                    'cur_weather': cur_weather,
                    'weather_description': weather_description,
                    'humidity': humidity,
                    'pressure': ceil(pressure / 1.333),  # Конвертируем давление в мм рт.ст.
                    'wind_speed': wind_speed,
                    'sunrise_time': sunrise_time,
                    'sunset_time': sunset_time,
                    'length_day_hours': length_day_hours,
                    'length_day_minutes': length_day_minutes,
                    'city_timezone': city_timezone,
                }
            else:
                return None
    except httpx.HTTPError as http_err:
        print(f"Произошла ошибка HTTP: {http_err}")
        return None
    except Exception as e:
        print(f"Произошла ошибка: {e}")
        return None

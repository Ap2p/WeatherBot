from datetime import datetime
from environs import Env
from aiogram import Bot, Dispatcher, types
from aiogram.types import ParseMode
from aiogram.utils import executor
from translations import translations
from weather import get_weather_data
from loguru import logger

env = Env()
env.read_env()

bot_token = env('BOT_TOKEN')
API_KEY = env('API_KEY')

bot = Bot(token=bot_token)
dp = Dispatcher(bot)

# Configure loguru logger
logger.add("app.log", rotation="500 MB", retention="7 days", level="DEBUG")


async def start_command(msg: types.Message):
    keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True)
    keyboard.add(types.KeyboardButton(text='🌐 Language'))
    await msg.reply('Привет! Напиши мне название города, и я пришлю сводку погоды', reply_markup=keyboard)


async def handle_language_button(msg: types.Message):
    keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True)
    keyboard.add(types.KeyboardButton(text='🌐 Language'))

    if msg.text == '🌐 Language':
        inline_keyboard = types.InlineKeyboardMarkup(row_width=2)
        inline_keyboard.add(
            types.InlineKeyboardButton(text='English', callback_data='lang_en'),
            types.InlineKeyboardButton(text='Русский', callback_data='lang_ru')
        )

        await msg.reply(translations.get_translation('language_prompt', msg.from_user.language_code),
                        reply_markup=inline_keyboard)
    else:
        await msg.reply('Привет! Напиши мне название города, и я пришлю сводку погоды', reply_markup=keyboard)


async def handle_inline_buttons(query: types.CallbackQuery):
    query_data = query.data
    if query_data == 'lang_en':
        # Сохраняем выбранный язык пользователя
        user_language = 'en'
        translations.set_user_language(query.from_user.id, user_language)

        # Формируем сообщение с подтверждением смены языка
        confirmation_message = translations.get_translation('language_changed', user_language)
        await query.message.reply(confirmation_message)

    elif query_data == 'lang_ru':
        # Сохраняем выбранный язык пользователя
        user_language = 'ru'
        translations.set_user_language(query.from_user.id, user_language)

        # Формируем сообщение с подтверждением смены языка
        confirmation_message = translations.get_translation('language_changed', user_language)
        await query.message.reply(confirmation_message)


@dp.message_handler(commands=['start'])
async def start_command_wrapper(msg: types.Message):
    await start_command(msg)


@dp.message_handler(content_types=types.ContentTypes.TEXT, text='🌐 Language')
async def handle_language_button_wrapper(msg: types.Message):
    await handle_language_button(msg)


@dp.callback_query_handler(lambda query: True)
async def handle_inline_buttons_wrapper(query: types.CallbackQuery):
    await handle_inline_buttons(query)


@dp.message_handler(content_types=types.ContentTypes.TEXT)
async def get_weather(msg: types.Message):
    try:
        weather_data = await get_weather_data(msg.text, API_KEY)

        if weather_data:
            city_timezone = weather_data['city_timezone']
            datetime_now = datetime.now(city_timezone).strftime('%A %d-%m-%Y %H:%M')

            weather_message = (
                f"{datetime_now}\n"
                f"Погода в городе: {weather_data['city']}\n"
                f"Температура: {weather_data['cur_weather']} °C - {weather_data['weather_description']}\n"
                f"Влажность: {weather_data['humidity']}%\n"
                f"Давление: {weather_data['pressure']} мм.рт.ст\n"
                f"Ветер: {weather_data['wind_speed']} м/с\n"
                f"Восход солнца: {weather_data['sunrise_time']}\n"
                f"Закат солнца: {weather_data['sunset_time']}\n"
                f"Продолжительность дня: {weather_data['length_day_hours']} часов {weather_data['length_day_minutes']} минут\n"
                f"Хорошего дня! 👋"
            )

            await msg.reply(weather_message, parse_mode=ParseMode.HTML)
        else:
            await msg.reply('Не удалось получить информацию о погоде для данного города.')
    except Exception as e:
        # Log any exceptions that occur during weather data retrieval
        logger.exception(f"An error occurred while fetching weather data: {e}")
        await msg.reply('Произошла ошибка. Пожалуйста, попробуйте еще раз')


if __name__ == '__main__':
    executor.start_polling(dp)

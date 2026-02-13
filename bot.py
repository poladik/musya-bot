"""
🎬 КИНЕМАТОГРАФИЧНЫЙ РОМАНТИЧЕСКИЙ БОТ
Версия для облачного хостинга (Render.com)
Работает 24/7 без твоего компьютера!
"""

import asyncio
import random
import os  # ⚠️ ВАЖНО: для чтения токена из переменных окружения
from datetime import datetime, date
from aiogram import Bot, Dispatcher, F, types
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup, FSInputFile

# ============================================================================
# ⚙️ НАСТРОЙКИ
# ============================================================================

# 🔑 Токен теперь берётся из переменных окружения (для безопасности)
BOT_TOKEN = os.environ.get("BOT_TOKEN", "8295640025:AAFnlqLYIAcJBVzZwNM7QMnbWLl7OU498QU")

# 🔐 Пароль
PASSWORD = "14.09.2002"

# 💌 Письмо
LETTER_TEXT = """
Письмо моей будущей жене.

Муся,

иногда я думаю о нас и понимаю одну простую вещь — 
я не боюсь ссор. 
Я боюсь только одного: потерять тебя из-за них.

Если однажды мы будем злиться друг на друга, 
если слова станут резкими, 
я всё равно сделаю всё, чтобы снова и снова выбирать тебя. 
Даже если буду считать, что прав. 
Даже если будет тяжело. 
Потому что для меня «мы» важнее, чем моя гордость.

Я очень не хочу, чтобы ты плакала из-за меня.
Если тебе больно — подойди ко мне.
Если тяжело — скажи.
Если внутри всё рушится — дай мне быть тем, кто будет держать.

Балам, тебе не надо быть сильной рядом со мной.
Мне нужна настоящая ты.
Та, которая может быть разной.
И радостной, и уставшей, и капризной, и ранимой.

Со мной тебе не нужно быть стойкой.
Стойким буду я.

И знаешь, что для меня главное?
Семья… которую мы создадим.
И я хочу, чтобы ты никогда не чувствовала себя в моём доме чужой.
Потому что мой дом — в первую очередь это ты.

И сколько бы у нас ни было детей, 
ты всё равно останешься для меня первым ребёнком, 
ведь за тебя я молюсь точно также...
"""

# 📅 Наша дата
START_DATE = date(2025, 10, 18)

# 📍 Координаты Galata Kulesi
GALATA_LATITUDE = 41.0256
GALATA_LONGITUDE = 28.9742

# Текст для локации
LOCATION_TEXT = """
Говорят, по легенде, с кем поднимешься на Галатскую башню в Стамбуле, с тем и проживёшь всю жизнь.

Я бы хотел, чтобы однажды это место стало нашим — тем, куда мы поднимемся вместе.
"""

# ============================================================================
# РОМАНТИЧЕСКИЕ СООБЩЕНИЯ
# ============================================================================

LONGING_MESSAGES = [
    "Сегодня ветер. И я подумал, что если бы ты была рядом, мы бы пили чай и смотрели, как качаются шторы.",
    "Я поймал себя на том, что улыбаюсь в пустоту. Просто вспомнил, как ты смеёшься.",
    "Знаешь, расстояние — это странная вещь. Оно ничего не уменьшает. Наоборот — увеличивает.",
    "Иногда я специально не пишу первым. Чтобы ты написала. И каждый раз, когда вижу уведомление, мне 17.",
    "Здесь сейчас закат. И я в тысячный раз думаю: хорошо бы ты это видела.",
    "Я заметил: когда скучаю, начинаю говорить с тобой вслух. Потом вспоминаю, что тебя нет рядом. Потом снова говорю.",
    "Мне не нужен тайм-менеджмент. Мне нужен тайм-с-тобой-менеджмент.",
    "Ты не представляешь, как много места ты занимаешь в моей голове. И я не хочу освобождать его.",
    "Я перечитываю наши старые переписки. Ты тогда написала 'спокойной ночи', а я не ответил. Прости меня за этого идиота.",
    "Сегодня мне приснилось, что ты рядом. Проснулся и долго не мог понять, почему ты не спишь рядом."
]

# ============================================================================
# ИНИЦИАЛИЗАЦИЯ
# ============================================================================

class AuthStates(StatesGroup):
    waiting_for_password = State()
    blocked = State()

storage = MemoryStorage()
bot = Bot(token=BOT_TOKEN)
dp = Dispatcher(storage=storage)

authorized_users = set()
failed_attempts = {}
blocked_until = {}

# ============================================================================
# КЛАВИАТУРА
# ============================================================================

def get_main_menu_keyboard():
    buttons = [
        [InlineKeyboardButton(text="✉️ Письмо", callback_data="letter")],
        [InlineKeyboardButton(text="📍 Galata Kulesi", callback_data="location")],
        [InlineKeyboardButton(text="🌙 Если скучаешь", callback_data="longing")],
        [InlineKeyboardButton(text="💫 Счетчик отношений", callback_data="our_day")]
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)

# ============================================================================
# ВСПОМОГАТЕЛЬНЫЕ ФУНКЦИИ
# ============================================================================

async def send_with_pause(message: types.Message, text: str, pause: float = 0.7):
    await bot.send_chat_action(message.chat.id, action="typing")
    await asyncio.sleep(pause)
    await message.answer(text)

async def send_long_text(message: types.Message, text: str):
    parts = text.strip().split('\n\n')
    for i, part in enumerate(parts):
        await bot.send_chat_action(message.chat.id, action="typing")
        await asyncio.sleep(0.8 if i == 0 else 0.4)
        await message.answer(part.strip())

# ============================================================================
# КОМАНДА START
# ============================================================================

@dp.message(Command("start"))
async def cmd_start(message: types.Message, state: FSMContext):
    user_id = message.from_user.id
    
    # Проверка блокировки
    if user_id in blocked_until:
        if datetime.now().timestamp() < blocked_until[user_id]:
            remaining = int((blocked_until[user_id] - datetime.now().timestamp()) / 60)
            await message.answer(f"⏳ Подожди {remaining} мин")
            return
        else:
            del blocked_until[user_id]
            del failed_attempts[user_id]
    
    # Если уже авторизован
    if user_id in authorized_users:
        await send_with_pause(message, "🍃 С возвращением...")
        await asyncio.sleep(0.8)
        await message.answer("Выбери:", reply_markup=get_main_menu_keyboard())
        return
    
    # Запрос пароля
    await message.answer("🔐 Напиши пароль:")
    await state.set_state(AuthStates.waiting_for_password)

# ============================================================================
# ОБРАБОТЧИК ПАРОЛЯ
# ============================================================================

@dp.message(AuthStates.waiting_for_password)
async def process_password(message: types.Message, state: FSMContext):
    user_id = message.from_user.id
    
    if user_id not in failed_attempts:
        failed_attempts[user_id] = 0
    
    if message.text == PASSWORD:
        authorized_users.add(user_id)
        failed_attempts[user_id] = 0
        await state.clear()
        
        await bot.send_chat_action(message.chat.id, action="typing")
        await asyncio.sleep(1.2)
        
        await message.answer("🍃 Муся, ты сейчас в месте,\nкоторое существует только для нас.")
        await asyncio.sleep(1.5)
        await bot.send_chat_action(message.chat.id, action="typing")
        await asyncio.sleep(0.8)
        await message.answer("Здесь нет расстояния.\n\n───────")
        await asyncio.sleep(0.8)
        await message.answer("Выбери:", reply_markup=get_main_menu_keyboard())
        
    else:
        failed_attempts[user_id] += 1
        remaining = 3 - failed_attempts[user_id]
        
        if failed_attempts[user_id] >= 3:
            block_time = datetime.now().timestamp() + 300
            blocked_until[user_id] = block_time
            await state.clear()
            await message.answer("⏸ 3 неверные попытки. Подожди 5 минут.")
        else:
            await message.answer(f"❌ Неверный пароль.\nОсталось попыток: {remaining}")

# ============================================================================
# КНОПКА: ✉️ ПИСЬМО
# ============================================================================

@dp.callback_query(F.data == "letter")
async def process_letter(callback: types.CallbackQuery):
    user_id = callback.from_user.id
    
    if user_id not in authorized_users:
        await callback.answer("🔐 Нужен пароль", show_alert=True)
        return
    
    await callback.answer()
    await send_long_text(callback.message, LETTER_TEXT)

# ============================================================================
# КНОПКА: 📍 GALATA KULESI
# ============================================================================

@dp.callback_query(F.data == "location")
async def process_location(callback: types.CallbackQuery):
    user_id = callback.from_user.id
    
    if user_id not in authorized_users:
        await callback.answer("🔐 Нужен пароль", show_alert=True)
        return
    
    await callback.answer()
    
    try:
        photo_url = "https://upload.wikimedia.org/wikipedia/commons/thumb/9/9c/Galata_Tower_%28Galata_Kulesi%29%2C_Istanbul_%2836788128494%29.jpg/800px-Galata_Tower_%28Galata_Kulesi%29%2C_Istanbul_%2836788128494%29.jpg"
        await callback.message.answer_photo(
            photo=photo_url,
            caption="🏰 Galata Kulesi"
        )
    except:
        await callback.message.answer("🏰 Galata Kulesi")
    
    await asyncio.sleep(0.5)
    await callback.message.answer_location(
        latitude=GALATA_LATITUDE,
        longitude=GALATA_LONGITUDE
    )
    await asyncio.sleep(0.5)
    await send_long_text(callback.message, LOCATION_TEXT)

# ============================================================================
# КНОПКА: 🌙 ЕСЛИ СКУЧАЕШЬ
# ============================================================================

@dp.callback_query(F.data == "longing")
async def process_longing(callback: types.CallbackQuery):
    user_id = callback.from_user.id
    
    if user_id not in authorized_users:
        await callback.answer("🔐 Нужен пароль", show_alert=True)
        return
    
    await callback.answer()
    message = random.choice(LONGING_MESSAGES)
    await send_with_pause(callback.message, message, pause=1.0)

# ============================================================================
# КНОПКА: 💫 СЧЕТЧИК ОТНОШЕНИЙ
# ============================================================================

@dp.callback_query(F.data == "our_day")
async def process_our_day(callback: types.CallbackQuery):
    user_id = callback.from_user.id
    
    if user_id not in authorized_users:
        await callback.answer("🔐 Нужен пароль", show_alert=True)
        return
    
    await callback.answer()
    
    today = date.today()
    days_passed = (today - START_DATE).days
    
    if days_passed >= 0:
        years = days_passed // 365
        months = (days_passed % 365) // 30
        days = (days_passed % 365) % 30
        
        text = f"💫 <b>Наши отношения</b>\n\n"
        text += f"❤️ <b>{days_passed}</b> день\n\n"
        
        if years > 0:
            text += f"📅 {years} лет"
        if months > 0:
            text += f", {months} месяцев"
        if days > 0 and years == 0:
            text += f", {days} дней"
        
        text += f"\n\nИ я всё ещё хочу тебя рядом."
        
        await send_with_pause(callback.message, text, pause=1.0)
    else:
        await send_with_pause(
            callback.message,
            f"💫 Мы ещё не встретились в этом дне.\nНо я уже жду тебя.",
            pause=0.8
        )

# ============================================================================
# ТЕКСТОВЫЕ СООБЩЕНИЯ
# ============================================================================

@dp.message(F.text)
async def process_text_messages(message: types.Message):
    user_id = message.from_user.id
    text = message.text.lower().strip()
    
    if user_id not in authorized_users:
        return
    
    if message.text.strip() == "14.09.2002":
        await bot.send_chat_action(message.chat.id, action="typing")
        await asyncio.sleep(1.2)
        await message.answer("Да.\nВ тот день я даже не знал,\nнасколько ты станешь важной.")
        await asyncio.sleep(1.5)
        await bot.send_chat_action(message.chat.id, action="typing")
        await asyncio.sleep(0.8)
        await message.answer("И я бы написал тебе снова.")
        return
    
    await bot.send_chat_action(message.chat.id, action="typing")
    await asyncio.sleep(0.5)
    await message.answer("🍃 Я здесь. Просто пиши.")

# ============================================================================
# ЗАПУСК
# ============================================================================

async def main():
    print("🎬 БОТ ЗАПУЩЕН В ОБЛАКЕ")
    print("━━━━━━━━━━━━━━━━━━━━━━━")
    print("✅ Бот будет работать 24/7")
    print("✅ Компьютер можно выключить")
    print("━━━━━━━━━━━━━━━━━━━━━━━")
    
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
import aiosqlite
from aiogram import Bot, Dispatcher, types
from aiogram.contrib.middlewares.logging import LoggingMiddleware
from aiogram.utils import executor
from aiogram.dispatcher.filters import Command

API_TOKEN = '7037813515:AAGOQxlALQBuNmOn3KxvM3r1q78Nd6D9Ews'

# Initialize bot and dispatcher
bot = Bot(token=API_TOKEN)
dp = Dispatcher(bot)
dp.middleware.setup(LoggingMiddleware())

# Allowed user IDs for the /setcard command
ALLOWED_USER_IDS = [6385046213, 516337879]

# Database initialization
async def init_db():
    async with aiosqlite.connect('cards.db') as db:
        await db.execute('''
            CREATE TABLE IF NOT EXISTS cards (
                id INTEGER PRIMARY KEY,
                card TEXT NOT NULL
            )
        ''')
        await db.commit()

# Set bot commands
async def set_commands(bot: Bot):
    commands = [
        types.BotCommand(command="/card", description="Получить текущую карту"),
        types.BotCommand(command="/setcard", description="Установить новую карту (Только для админа)")
    ]
    await bot.set_my_commands(commands)

# Command to get the current card
@dp.message_handler(commands=['card'])
async def get_card(message: types.Message):
    async with aiosqlite.connect('cards.db') as db:
        async with db.execute('SELECT card FROM cards ORDER BY id DESC LIMIT 1') as cursor:
            row = await cursor.fetchone()
            current_card = row[0] if row else "Карта не установленна"
    await message.reply(f'''{current_card}''', parse_mode=types.ParseMode.MARKDOWN)

# Command to set a new card
@dp.message_handler(commands=['setcard'])
async def set_card(message: types.Message):
    user_id = message.from_user.id
    if user_id in ALLOWED_USER_IDS:
        args = message.get_args()
        if args:
            async with aiosqlite.connect('cards.db') as db:
                await db.execute('INSERT INTO cards (card) VALUES (?)', (args,))
                await db.commit()
            await message.reply(f"Карта обновлена на: {args}")
        else:
            await message.reply("Пожалуйста введите карту в таком формате. Используя: /setcard <new_card>")
    else:
        await message.reply("У тебя нет прав чтобы это делать.")

if __name__ == '__main__':
    import asyncio
    loop = asyncio.get_event_loop()
    loop.run_until_complete(init_db())
    loop.run_until_complete(set_commands(bot))
    executor.start_polling(dp, skip_updates=True)

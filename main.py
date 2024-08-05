import aiosqlite
from aiogram import Bot, Dispatcher, types
from aiogram.contrib.middlewares.logging import LoggingMiddleware
from aiogram.utils import executor
from aiogram.dispatcher.filters import Command
import datetime

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
                card TEXT NOT NULL,
                card_name TEXT NOT NULL,
                bank_name TEXT NOT NULL
            )
        ''')
        await db.execute('''
           CREATE TABLE IF NOT EXISTS earnings (
               id INTEGER PRIMARY KEY AUTOINCREMENT,
               amount REAL NOT NULL,
               date TEXT NOT NULL
           )
       ''')
        await db.commit()

# Set bot commands
async def set_commands(bot: Bot):
    commands = [
        types.BotCommand(command="/card", description="Получить текущую карту"),
        types.BotCommand(command="/todayearnings", description="Показать заработанную сумму за сегодня"),

        types.BotCommand(command="/setcard", description="Установить новую карту (Только для админа)"),
        types.BotCommand(command="/addearn", description="Добавить заработанную сумму (Только для админа)"),
        types.BotCommand(command="/removeearn", description="Отнять сумму от заработанного (Только для админа)")
    ]
    await bot.set_my_commands(commands)

@dp.message_handler(content_types=types.ContentType.NEW_CHAT_MEMBERS)
async def welcome_new_member(message: types.Message):
    for new_member in message.new_chat_members:
        await message.answer(f"Добро пожаловать, @{new_member.username}!")

@dp.message_handler(commands=['card'])
async def get_card(message: types.Message):
    async with aiosqlite.connect('cards.db') as db:
        async with db.execute('SELECT card_name, card, bank_name FROM cards ORDER BY id DESC LIMIT 1') as cursor:
            row = await cursor.fetchone()
            if row:
                card_name, card, bank_name = row
                await message.reply(f'''💳 Карты для переводов

🇷🇺{card}
├ От 100
├ {card_name}
└ {bank_name}

⚠️ Осторожно, вам может написать фейк, актуальные реквизиты указаны исключительно в этом сообщении. Будьте внимательны и отправляйте чеки в лс @papa_payments''',
                                    parse_mode=types.ParseMode.HTML)
            else:
                await message.reply("Карта не установленна")

# Command to set a new card
@dp.message_handler(commands=['setcard'])
async def set_card(message: types.Message):
    user_id = message.from_user.id
    if user_id in ALLOWED_USER_IDS:
        args = message.get_args().split(maxsplit=2)
        if len(args) == 3:
            card_name, card, bank_name = args
            async with aiosqlite.connect('cards.db') as db:
                await db.execute('INSERT INTO cards (card_name, card, bank_name) VALUES (?, ?, ?)', (card_name, card, bank_name))
                await db.commit()
            await message.reply(f"Карта обновлена на: {card_name} - {card} - {bank_name}")
        else:
            await message.reply("Пожалуйста введите карту в таком формате. Используя: /setcard <card_name> <card> <bank_name>")
    else:
        await message.reply("У тебя нет прав чтобы это делать.")

@dp.message_handler(commands=['addearn'])
async def add_earn(message: types.Message):
    user_id = message.from_user.id
    if user_id in ALLOWED_USER_IDS:
        args = message.get_args().split()
        if len(args) == 1 and args[0].replace('.', '', 1).isdigit():
            amount = float(args[0])
            date = datetime.date.today().isoformat()
            async with aiosqlite.connect('cards.db') as db:
                await db.execute('INSERT INTO earnings (amount, date) VALUES (?, ?)', (amount, date))
                await db.commit()
            await message.reply(f"Сумма {amount} добавлена за {date}")
        else:
            await message.reply("Пожалуйста введите сумму в таком формате: /addearn <amount>")
    else:
        await message.reply("У тебя нет прав чтобы это делать.")

@dp.message_handler(commands=['removeearn'])
async def remove_earn(message: types.Message):
    user_id = message.from_user.id
    if user_id in ALLOWED_USER_IDS:
        args = message.get_args().split()
        if len(args) == 1 and args[0].replace('.', '', 1).isdigit():
            amount = float(args[0])
            date = datetime.date.today().isoformat()
            async with aiosqlite.connect('cards.db') as db:
                await db.execute('INSERT INTO earnings (amount, date) VALUES (?, ?)', (-amount, date))
                await db.commit()
            await message.reply(f"Сумма {amount} отнята за {date}")
        else:
            await message.reply("Пожалуйста введите сумму в таком формате: /removeearn <amount>")
    else:
        await message.reply("У тебя нет прав чтобы это делать.")

@dp.message_handler(commands=['todayearnings'])
async def today_earnings(message: types.Message):
    today = datetime.date.today().isoformat()
    async with aiosqlite.connect('cards.db') as db:
        async with db.execute('SELECT SUM(amount) FROM earnings WHERE date = ?', (today,)) as cursor:
            row = await cursor.fetchone()
            total = row[0] if row[0] is not None else 0
            await message.reply(f"Общая сумма заработанная за сегодня: {total:.2f}")

if __name__ == '__main__':
    import asyncio
    loop = asyncio.get_event_loop()
    loop.run_until_complete(init_db())
    loop.run_until_complete(set_commands(bot))
    executor.start_polling(dp, skip_updates=True)

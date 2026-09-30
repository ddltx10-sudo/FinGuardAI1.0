import asyncio

from aiogram import Bot, Dispatcher, F
from aiogram.filters import Command
from aiogram.types import Message, ReplyKeyboardMarkup, KeyboardButton

from config import BOT_TOKEN
from api import get_market_analysis
from ai import ask_ai, analyze_market
from formatter import clean_ai_text

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

main_keyboard = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="📊 Анализ актива"), KeyboardButton(text="🤖 AI-вопрос")],
        [KeyboardButton(text="🔍 Проверить BTC"), KeyboardButton(text="🔍 Проверить ETH")],
        [KeyboardButton(text="🧮 Калькулятор"), KeyboardButton(text="🌐 Актуальный поиск")],
        [KeyboardButton(text="ℹ️ Помощь")],
    ],
    resize_keyboard=True,
)


def split_message(text: str, max_length: int = 3800) -> list[str]:
    return [text[i:i + max_length] for i in range(0, len(text), max_length)] or [""]


async def send_long_message(message: Message, text: str):
    for part in split_message(text):
        await message.answer(part)


@dp.message(Command("start"))
async def start_command(message: Message):
    await message.answer(
        "FinGuard AI\n\n"
        "Интеллектуальный финансовый помощник.\n\n"
        "Доступные функции:\n"
        "• анализ криптовалют;\n"
        "• AI-ответы на финансовые вопросы;\n"
        "• финансовые расчёты;\n"
        "• поиск финансовой информации;\n"
        "• выявление потенциальных рыночных аномалий.\n\n"
        "Выберите действие ниже:",
        reply_markup=main_keyboard,
    )


@dp.message(Command("help"))
async def help_command(message: Message):
    await message.answer(
        "FinGuard AI — справка\n\n"
        "Анализ актива: отправьте BTC, ETH или другой тикер.\n\n"
        "AI-вопрос: задайте финансовый вопрос обычным языком.\n\n"
        "Калькулятор: отправьте финансовый расчёт.\n\n"
        "Актуальный поиск: задайте вопрос о финансовой информации."
    )


@dp.message(F.text == "🔍 Проверить BTC")
async def btc_button(message: Message):
    await scan_asset(message, "BTC")


@dp.message(F.text == "🔍 Проверить ETH")
async def eth_button(message: Message):
    await scan_asset(message, "ETH")


@dp.message(F.text == "📊 Анализ актива")
async def analyze_button(message: Message):
    await message.answer("Введите тикер актива, например BTC, ETH или SOL.")


@dp.message(F.text == "🤖 AI-вопрос")
async def ai_button(message: Message):
    await message.answer("Задайте финансовый вопрос обычным языком.")


@dp.message(F.text == "🧮 Калькулятор")
async def calculator_button(message: Message):
    await message.answer(
        "Введите расчёт обычным языком.\n\n"
        "Примеры:\n"
        "15% от 500000\n"
        "Депозит 1000000 под 15% на 3 года\n"
        "Кредит 5000000 под 18% на 5 лет"
    )


@dp.message(F.text == "🌐 Актуальный поиск")
async def search_button(message: Message):
    await message.answer("Введите финансовый вопрос для анализа.")


@dp.message(F.text == "ℹ️ Помощь")
async def help_button(message: Message):
    await help_command(message)


@dp.message(Command("ask"))
async def ask_command(message: Message):
    question = message.text.replace("/ask", "", 1).strip()
    if not question:
        await message.answer("Введите вопрос после команды /ask.")
        return
    result = clean_ai_text(ask_ai(question))
    await send_long_message(message, result)


async def scan_asset(message: Message, symbol: str):
    await message.answer(f"Анализирую {symbol}...")
    try:
        data = await get_market_analysis(symbol)
        text = (
            "FinGuard AI\n\n"
            f"Актив: {data['symbol']}\n"
            f"Цена: {data['price']:.8f}\n"
            f"Изменение за 24ч: {data['change_24h']:.2f}%\n"
            f"Объём: {data['volume']:.2f}\n\n"
            f"SMA20: {data['sma20']:.4f}\n"
            f"SMA50: {data['sma50']:.4f}\n"
            f"EMA20: {data['ema20']:.4f}\n"
            f"RSI: {data['rsi']:.2f}\n"
            f"Волатильность: {data['volatility']:.2f}%\n"
            f"Volume ratio: {data['volume_ratio']:.2f}x\n\n"
            f"Тренд: {data['trend']}\n"
            f"Anomaly Score: {data['anomaly_score']}/100"
        )
        await send_long_message(message, text)
        await message.answer("Формирую AI-анализ...")
        await send_long_message(message, analyze_market(data))
    except Exception as error:
        print("SCAN ERROR:", repr(error))
        await message.answer("Не удалось получить данные. Проверьте тикер и попробуйте ещё раз.")


@dp.message(F.text)
async def text_handler(message: Message):
    text = message.text.strip()
    buttons = {
        "📊 Анализ актива", "🤖 AI-вопрос", "🔍 Проверить BTC", "🔍 Проверить ETH",
        "🧮 Калькулятор", "🌐 Актуальный поиск", "ℹ️ Помощь",
    }
    if text in buttons:
        return

    clean = text.upper().replace("/", "").replace("-", "")
    if len(clean) <= 10 and clean.isalpha():
        try:
            await scan_asset(message, clean)
            return
        except Exception:
            pass

    await message.answer("Обрабатываю запрос...")
    await send_long_message(message, clean_ai_text(ask_ai(text)))


async def main():
    print("FinGuard AI запущен")
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())

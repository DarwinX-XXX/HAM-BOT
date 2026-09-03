import asyncio
import logging
import json
from aiogram import Bot, Dispatcher, F, types
from aiogram.filters import CommandStart
from aiogram.types import (
    InlineKeyboardMarkup,
    InlineKeyboardButton,
    WebAppInfo,
    LabeledPrice,
    PreCheckoutQuery,
)

# === НАСТРОЙКИ (ЗАПОЛНИТЕ СВОИ ДАННЫЕ) ===
BOT_TOKEN = "ВАШ_BOT_TOKEN_ОТ_BOTFATHER"
PAYMENT_PROVIDER_TOKEN = "ВАШ_PAYMENT_TOKEN"  # Токен ЮKassa/Сбербанк из BotFather (или "" для теста)
WEB_APP_URL = "https://ваш-домен.com/index.html"  # Прямая HTTPS-ссылка на ваш загруженный index.html

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()


@dp.message(CommandStart())
async def cmd_start(message: types.Message):
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(
            text="🛒 Открыть магазин",
            web_app=WebAppInfo(url=WEB_APP_URL)
        )]
    ])
    await message.answer(
        "Привет! Нажмите кнопку ниже, чтобы открыть каталог Mini App:",
        reply_markup=kb
    )


# Обработка корзины, отправленной из Mini App
@dp.message(F.web_app_data)
async def handle_webapp_data(message: types.Message):
    data = json.loads(message.web_app_data.data)

    if data.get("action") == "checkout":
        cart_items = data.get("items", {})

        prices = []
        text_summary = "<b>Ваш заказ:</b>\n\n"
        total_amount = 0

        for item_id, item in cart_items.items():
            item_total = item['price'] * item['count']
            total_amount += item_total
            text_summary += f"• {item['name']} x{item['count']} — {item_total} руб.\n"
            prices.append(LabeledPrice(label=f"{item['name']} x{item['count']}", amount=item_total * 100))

        text_summary += f"\n<b>Итого к оплате: {total_amount} руб.</b>"

        # Если токен оплаты указан — выставляем счёт в чат
        if PAYMENT_PROVIDER_TOKEN:
            await bot.send_invoice(
                chat_id=message.chat.id,
                title="Оплата заказа",
                description="Оплата товаров из магазина",
                payload=f"order_{message.from_user.id}",
                provider_token=PAYMENT_PROVIDER_TOKEN,
                currency="RUB",
                prices=prices
            )
        else:
            await message.answer(
                f"{text_summary}\n\n<i>(Режим теста: PAYMENT_PROVIDER_TOKEN не указан)</i>",
                parse_mode="HTML"
            )


@dp.pre_checkout_query()
async def process_pre_checkout(pre_checkout_query: PreCheckoutQuery):
    await bot.answer_pre_checkout_query(pre_checkout_query.id, ok=True)


@dp.message(F.successful_payment)
async def process_successful_payment(message: types.Message):
    await message.answer("✅ <b>Оплата прошла успешно!</b>\nВаш заказ принят в работу.", parse_mode="HTML")


async def main():
    logging.basicConfig(level=logging.INFO)
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
import asyncio
import logging
from io import BytesIO
from contextlib import asynccontextmanager

import qrcode

from fastapi import FastAPI

from telegram import (
    Bot,
    Update,
    ReplyKeyboardMarkup,
    KeyboardButton,
)


# =====================================
# CONFIGURATION
# =====================================

BOT_TOKEN = "YOUR_NEW_BOT_TOKEN"

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)

logger = logging.getLogger(__name__)

bot = Bot(token=BOT_TOKEN)

# ذخیره تنظیمات کاربران
user_data = {}

polling_task = None


# =====================================
# COLORS
# =====================================

COLORS = {
    "⚫ مشکی": "#000000",
    "🔵 آبی": "#1565C0",
    "🔴 قرمز": "#D32F2F",
    "🟢 سبز": "#2E7D32",
    "🟣 بنفش": "#7B1FA2",
    "🟠 نارنجی": "#EF6C00",
    "🩷 صورتی": "#E91E63",
    "🟤 قهوه‌ای": "#795548",
}


# =====================================
# MAIN MENU
# =====================================

MAIN_MENU = ReplyKeyboardMarkup(
    [
        [KeyboardButton("✨ ساخت QR Code")],
        [KeyboardButton("🎨 انتخاب رنگ QR")],
        [
            KeyboardButton("ℹ️ راهنمای استفاده"),
            KeyboardButton("🔄 شروع مجدد"),
        ],
    ],
    resize_keyboard=True,
    is_persistent=True,
    input_field_placeholder="یک گزینه را انتخاب کنید..."
)


# =====================================
# COLOR MENU
# =====================================

COLOR_MENU = ReplyKeyboardMarkup(
    [
        [
            KeyboardButton("⚫ مشکی"),
            KeyboardButton("🔵 آبی"),
        ],
        [
            KeyboardButton("🔴 قرمز"),
            KeyboardButton("🟢 سبز"),
        ],
        [
            KeyboardButton("🟣 بنفش"),
            KeyboardButton("🟠 نارنجی"),
        ],
        [
            KeyboardButton("🩷 صورتی"),
            KeyboardButton("🟤 قهوه‌ای"),
        ],
        [
            KeyboardButton("↩️ بازگشت"),
        ],
    ],
    resize_keyboard=True,
    input_field_placeholder="رنگ QR را انتخاب کنید..."
)


# =====================================
# QR GENERATOR
# =====================================

def make_qr(text, color):

    qr = qrcode.QRCode(
        version=None,
        error_correction=qrcode.constants.ERROR_CORRECT_M,
        box_size=12,
        border=4,
    )

    qr.add_data(text)
    qr.make(fit=True)

    image = qr.make_image(
        fill_color=color,
        back_color="white",
    )

    buffer = BytesIO()

    image.save(buffer, format="PNG")

    buffer.seek(0)
    buffer.name = "qrcode.png"

    return buffer


# =====================================
# START COMMAND
# =====================================

async def start(chat_id, user_id):

    if user_id not in user_data:

        user_data[user_id] = {
            "mode": None,
            "color": "#000000",
        }

    user_data[user_id]["mode"] = None

    await bot.send_message(
        chat_id=chat_id,

        text=(
            "✨ به QR CODE BOT خوش آمدید!\n\n"

            "🚀 با این ربات می‌توانید اطلاعات خود را "
            "به QR Code تبدیل کنید.\n\n"

            "📝 تبدیل متن و لینک\n"
            "🎨 انتخاب رنگ اختصاصی\n"
            "📸 دریافت QR به‌صورت تصویر\n\n"

            "━━━━━━━━━━━━━━━━\n"
            "👇 از منوی زیر استفاده کنید:"
        ),

        reply_markup=MAIN_MENU,
    )


# =====================================
# TEXT QR GENERATION
# =====================================

async def create_qr(chat_id, user_id, text):

    text = text.strip()

    if not text:
        return

    if len(text) > 2000:

        await bot.send_message(
            chat_id=chat_id,
            text=(
                "⚠️ متن شما بیش از حد طولانی است.\n"
                "لطفاً متن کوتاه‌تری ارسال کنید."
            ),
        )

        return

    color = user_data[user_id].get(
        "color",
        "#000000",
    )

    try:

        qr_image = make_qr(text, color)

        await bot.send_photo(
            chat_id=chat_id,

            photo=qr_image,

            caption=(
                "✅ QR Code شما با موفقیت ساخته شد!\n\n"
                "🎨 رنگ انتخابی: "
                f"{color}\n\n"
                "برای ساخت QR جدید، اطلاعات دیگری ارسال کنید."
            ),
        )

    except Exception:

        logger.exception("QR generation error")

        await bot.send_message(
            chat_id=chat_id,
            text=(
                "❌ ساخت QR با مشکل مواجه شد.\n"
                "لطفاً متن دیگری امتحان کنید."
            ),
        )


# =====================================
# MESSAGE HANDLER
# =====================================

async def handle_message(chat_id, user_id, text):

    if user_id not in user_data:

        user_data[user_id] = {
            "mode": None,
            "color": "#000000",
        }

    text = text.strip()

    # CREATE QR

    if text == "✨ ساخت QR Code":

        user_data[user_id]["mode"] = "qr"

        await bot.send_message(
            chat_id=chat_id,

            text=(
                "📝 اطلاعات موردنظر را ارسال کنید.\n\n"

                "مثال:\n"
                "🌐 https://example.com\n"
                "📱 09121234567\n"
                "💬 سلام دنیا\n"
                "📍 آدرس موردنظر\n\n"

                "ربات اطلاعات شما را به QR تبدیل می‌کند."
            ),

            reply_markup=MAIN_MENU,
        )

        return

    # COLOR MENU

    elif text == "🎨 انتخاب رنگ QR":

        user_data[user_id]["mode"] = "color"

        await bot.send_message(
            chat_id=chat_id,

            text=(
                "🎨 رنگ موردنظر خود را انتخاب کنید:\n\n"
                "رنگ انتخابی برای QRهای بعدی شما استفاده می‌شود."
            ),

            reply_markup=COLOR_MENU,
        )

        return

    # COLOR SELECTION

    elif text in COLORS:

        user_data[user_id]["color"] = COLORS[text]

        user_data[user_id]["mode"] = None

        await bot.send_message(
            chat_id=chat_id,

            text=(
                f"✅ رنگ {text} انتخاب شد!\n\n"
                "از این به بعد QRهای شما با این رنگ ساخته می‌شوند."
            ),

            reply_markup=MAIN_MENU,
        )

        return

    # BACK

    elif text == "↩️ بازگشت":

        user_data[user_id]["mode"] = None

        await bot.send_message(
            chat_id=chat_id,
            text="🏠 به منوی اصلی برگشتید.",
            reply_markup=MAIN_MENU,
        )

        return

    # HELP

    elif text == "ℹ️ راهنمای استفاده":

        await bot.send_message(
            chat_id=chat_id,

            text=(
                "📚 راهنمای QR CODE BOT\n\n"

                "1️⃣ روی ساخت QR Code بزنید.\n"
                "2️⃣ متن، لینک یا شماره خود را ارسال کنید.\n"
                "3️⃣ تصویر QR را دریافت کنید.\n\n"

                "🎨 تغییر رنگ:\n"
                "از قسمت انتخاب رنگ، رنگ دلخواه خود را انتخاب کنید.\n\n"

                "💡 هر کاربر تنظیمات رنگ مستقل خودش را دارد.\n\n"

                "⚠️ برای اسکن بهتر QR، از رنگ‌های تیره "
                "روی پس‌زمینه سفید استفاده کنید."
            ),

            reply_markup=MAIN_MENU,
        )

        return

    # RESTART

    elif text == "🔄 شروع مجدد":

        user_data[user_id]["mode"] = None

        await start(chat_id, user_id)

        return

    # QR INPUT

    elif user_data[user_id].get("mode") == "qr":

        await create_qr(chat_id, user_id, text)

        return

    # UNKNOWN INPUT

    else:

        await bot.send_message(
            chat_id=chat_id,
            text="لطفاً ابتدا یکی از گزینه‌های منو را انتخاب کنید.",
            reply_markup=MAIN_MENU,
        )


# =====================================
# TELEGRAM POLLING
# =====================================

async def polling():

    offset = None

    logger.info("Telegram polling started")

    while True:

        try:

            updates = await bot.get_updates(
                offset=offset,
                timeout=30,
                allowed_updates=["message"],
                read_timeout=35,
            )

            for update in updates:

                offset = update.update_id + 1

                try:

                    if not update.message:
                        continue

                    message = update.message

                    if not message.from_user:
                        continue

                    chat_id = message.chat_id
                    user_id = message.from_user.id
                    text = message.text

                    if not text:
                        continue

                    # START COMMAND

                    if text.split()[0].split("@")[0] == "/start":

                        await start(chat_id, user_id)

                    # OTHER MESSAGES

                    else:

                        await handle_message(
                            chat_id,
                            user_id,
                            text,
                        )

                except Exception:

                    logger.exception(
                        "Message processing error"
                    )

        except asyncio.CancelledError:

            raise

        except Exception:

            logger.exception("Polling error")

            await asyncio.sleep(3)


# =====================================
# FASTAPI LIFESPAN
# =====================================

@asynccontextmanager
async def lifespan(app: FastAPI):

    global polling_task

    if BOT_TOKEN == "YOUR_NEW_BOT_TOKEN":
        raise ValueError("توکن ربات را وارد کنید.")

    await bot.initialize()

    # حذف Webhook قبلی در صورت وجود
    await bot.delete_webhook(
        drop_pending_updates=False
    )

    # شروع دریافت پیام‌ها
    polling_task = asyncio.create_task(
        polling()
    )

    logger.info("FASTAPI QR BOT STARTED")

    yield

    # توقف Polling
    polling_task.cancel()

    try:
        await polling_task

    except asyncio.CancelledError:
        pass

    await bot.shutdown()

    logger.info("BOT STOPPED")


# =====================================
# FASTAPI APPLICATION
# =====================================

app = FastAPI(
    title="QR Code Telegram Bot",
    description="Telegram QR Code Generator",
    version="1.0.0",
    lifespan=lifespan,
)


# =====================================
# HOME ENDPOINT
# =====================================

@app.get("/")
async def home():

    return {
        "status": "running",
        "service": "QR Code Telegram Bot",
        "framework": "FastAPI",
        "telegram": "Polling",
    }


# =====================================
# RUN
# =====================================

if __name__ == "__main__":

    import uvicorn

    uvicorn.run(
        app,
        host="127.0.0.1",
        port=8000,
    )
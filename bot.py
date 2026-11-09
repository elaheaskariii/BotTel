
import logging
from io import BytesIO

import qrcode


from telegram import Update
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    ContextTypes,
    filters,
)

BOT_TOKEN = "9032800212:AAE8mR435K5z2BifXFuxKsC60wESDkCJWqw"

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)


# =========================
# ساخت QR
# =========================
def make_qr(text: str) -> BytesIO:
    qr = qrcode.QRCode(
        error_correction=qrcode.constants.ERROR_CORRECT_M,
        box_size=10,
        border=4,
    )
    qr.add_data(text)
    qr.make(fit=True)
    img = qr.make_image(fill_color="black", back_color="white")
    buf = BytesIO()
    img.save(buf, format="PNG")
    buf.seek(0)
    return buf


# =========================
# هندلرها
# =========================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "سلام! 👋\n\n"
        "هر متن، لینک، شماره تلفن یا آدرسی بفرستی، برات QR کدش رو می‌سازم.\n\n"
        "مثال:\n"
        "https://example.com\n"
        "سلام دنیا\n"
        "09121234567"
    )


async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.strip()
    if not text:
        return

    if len(text) > 2000:
        await update.message.reply_text(
            "متنت خیلی بلنده (بیشتر از ۲۰۰۰ کاراکتر).\n"
            "QR کد ظرفیت محدودی داره."
        )
        return

    try:
        buf = make_qr(text)
        await update.message.reply_photo(
            photo=buf,
            caption="اینم QR کدت ✅",
        )
    except Exception as e:
        logging.exception("QR generation failed")
        await update.message.reply_text(f"خطا در ساخت QR: {e}")


# =========================
# اجرا
# =========================
def main():
    app = Application.builder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text))
    logging.info("ربات روشن شد (polling)...")
    app.run_polling()


if __name__ == "__main__":
    main()

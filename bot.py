import telebot
import os
import uuid
import cv2
import numpy as np
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton

TOKEN = "9032800212:AAE8mR435K5z2BifXFuxKsC60wESDkCJWqw"
bot = telebot.TeleBot(TOKEN)

TEMP_DIR = "temp_bot_images"
if not os.path.exists(TEMP_DIR):
    os.makedirs(TEMP_DIR)

def main_menu():
    markup = InlineKeyboardMarkup(row_width=1)
    btn1 = InlineKeyboardButton("🖼️ ارسال عکس برای حذف واترمارک", callback_data="send_photo")
    btn2 = InlineKeyboardButton("📖 راهنما", callback_data="help")
    markup.add(btn1, btn2)
    return markup

@bot.message_handler(commands=['start'])
def start(message):
    text = (
        "سلام 👋\n"
        "به ربات **حذف واترمارک** خوش آمدی.\n\n"
        "⚠️ **توجه:** به دلیل محدودیت کتابخانه، برای اینکه ربات بداند واترمارک کجاست، باید مختصات را وارد کنی.\n"
        "فرمت: `x,y,عرض,ارتفاع` (مثلاً `10,10,150,80`)\n"
        "اگر مطمئن نیستی، اول یک عکس بفرست تا ببینی چه اتفاقی می‌افتد."
    )
    bot.send_message(message.chat.id, text, reply_markup=main_menu(), parse_mode="Markdown")

@bot.callback_query_handler(func=lambda call: True)
def callback(call):
    if call.data == "help":
        bot.answer_callback_query(call.id)
        bot.send_message(call.message.chat.id, "عکس را بفرست و مختصات ناحیه واترمارک را با فرمت `x,y,w,h` در کپشن بنویس.")
    elif call.data == "send_photo":
        bot.answer_callback_query(call.id, "حالا عکست را بفرست 📤")

@bot.message_handler(content_types=['photo'])
def handle_photo(message):
    # پیش‌فرض: اگر کاربر مختصات نداده باشد، یک ناحیه تست در گوشه بالا-چپ
    coords = None
    if message.caption:
        try:
            parts = list(map(int, message.caption.strip().split(',')))
            if len(parts) == 4:
                coords = parts
        except:
            pass

    status = bot.reply_to(message, "⏳ دریافت شد، در حال پردازش...")
    input_path, output_path = None, None

    try:
        file_info = bot.get_file(message.photo[-1].file_id)
        downloaded = bot.download_file(file_info.file_path)
        uid = str(uuid.uuid4())
        input_path = os.path.join(TEMP_DIR, f"in_{uid}.jpg")
        output_path = os.path.join(TEMP_DIR, f"out_{uid}.jpg")

        with open(input_path, 'wb') as f:
            f.write(downloaded)

        img = cv2.imread(input_path)
        if img is None:
            raise ValueError("عکس خوانده نشد")

        h, w = img.shape[:2]

        # اگر مختصات داده نشده، یک ناحیه کوچک در گوشه بالا-چپ به عنوان تست
        if coords is None:
            x, y, wm_w, wm_h = 10, 10, 150, 80
        else:
            x, y, wm_w, wm_h = coords

        # محدود کردن مختصات به محدوده تصویر
        x = max(0, min(x, w-1))
        y = max(0, min(y, h-1))
        wm_w = max(1, min(wm_w, w-x))
        wm_h = max(1, min(wm_h, h-y))

        # ساخت ماسک
        mask = np.zeros((h, w), dtype=np.uint8)
        mask[y:y+wm_h, x:x+wm_w] = 255

        # استفاده از inpaint برای پر کردن
        result = cv2.inpaint(img, mask, inpaintRadius=3, flags=cv2.INPAINT_TELEA)
        cv2.imwrite(output_path, result)

        bot.edit_message_text("✅ پردازش انجام شد.", chat_id=message.chat.id, message_id=status.message_id)
        with open(output_path, 'rb') as f:
            bot.send_photo(message.chat.id, f, caption="نتیجه (ناحیه مشخص‌شده پاک شد)")

    except Exception as e:
        print(e)
        bot.edit_message_text(f"❌ خطا: {e}", chat_id=message.chat.id, message_id=status.message_id)
    finally:
        for p in [input_path, output_path]:
            if p and os.path.exists(p):
                os.remove(p)

print("ربات اجرا شد...")
bot.infinity_polling()
#
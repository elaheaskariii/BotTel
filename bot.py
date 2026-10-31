
import telebot

TOKEN = "9032800212:AAE8mR435K5z2BifXFuxKsC60wESDkCJWqw"
bot = telebot.TeleBot(TOKEN)

@bot.message_handler(commands=['start'])
def start(message):
    bot.reply_to(message, "سلام! چطور می‌تونم کمکت کنم؟")

@bot.message_handler(func=lambda m: m.text == "سلام")
def salam(message):
    bot.reply_to(message, "سلام، چطور می‌تونم کمکت کنم؟")

bot.infinity_polling()
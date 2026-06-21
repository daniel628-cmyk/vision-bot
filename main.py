import os
import sqlite3
import telebot
from deep_translator import GoogleTranslator
from telebot import types

TOKEN = os.environ.get('BOT_TOKEN')
bot = telebot.TeleBot(TOKEN)

ADMIN_ID = 5544893200

def init_db():
    conn = sqlite3.connect('bot_data.db')
    cursor = conn.cursor()
    cursor.execute('CREATE TABLE IF NOT EXISTS users (user_id INTEGER PRIMARY KEY)')
    conn.commit()
    conn.close()

init_db()

user_data = {}

lang_info = {
    "am": {"name": "አማርኛ", "flag": "🇪🇹"},
    "en": {"name": "English", "flag": "🇺🇸"},
    "om": {"name": "Oromiffa", "flag": "🌳"},
    "es": {"name": "Español", "flag": "🇪🇸"},
    "fr": {"name": "Français", "flag": "🇫🇷"},
    "ar": {"name": "العربية", "flag": "🇸🇦"},
    "de": {"name": "Deutsch", "flag": "🇩🇪"},
    "it": {"name": "Italiano", "flag": "🇮🇹"},
    "pt": {"name": "Português", "flag": "🇵🇹"},
    "ru": {"name": "Русский", "flag": "🇷🇺"},
    "zh-cn": {"name": "中文", "flag": "🇨🇳"},
    "ja": {"name": "日本語", "flag": "🇯🇵"}
}

# --- COMMAND HANDLERS ---

@bot.message_handler(commands=['start'])
def send_welcome(message):
    conn = sqlite3.connect('bot_data.db')
    cursor = conn.cursor()
    cursor.execute('INSERT OR IGNORE INTO users (user_id) VALUES (?)', (message.from_user.id,))
    conn.commit()
    conn.close()

    user_name = message.from_user.first_name
    welcome_text = (
        f"✨ **እንኳን ወደ Vision Translator በደህና መጡ!** ✨\n\n"
        f"ሰላም **{user_name}**! 👋\n"
        "ይህ ቦት ጽሑፎችን በቀላሉ ወደፈለጉት ዓለም አቀፍ ቋንቋዎች እንዲቀይሩ ይረዳዎታል። 🌍\n\n"
        "🚀 **ለመጀመር:** መተርጎም የሚፈልጉትን ጽሑፍ ይላኩልኝ!"
    )
    bot.reply_to(message, welcome_text, parse_mode='Markdown')

@bot.message_handler(commands=['about'])
def send_about(message):
    about_text = (
        "🤖 **ስለ Vision Translator Bot**\n\n"
        "🌐 የላቀ የትርጉም ቴክኖሎጂን በመጠቀም ጽሑፍን በሰከንዶች ውስጥ ይተርጉሙ።\n\n"
        "💎 **ቁልፍ ባህሪያት:**\n"
        "• ፈጣን እና ትክክለኛ ትርጉም\n"
        "• በርካታ የዓለም ቋንቋዎች ድጋፍ\n"
        "• ቀላል እና ምቹ አጠቃቀም\n\n"
        "📍 ስሪት: **1.1.0**"
    )
    bot.reply_to(message, about_text, parse_mode='Markdown')

@bot.message_handler(commands=['help'])
def send_help(message):
    help_text = (
        "💡 **የእገዛ ማዕከል** 🆘\n\n"
        "ቦቱን ለመጠቀም እነዚህን ደረጃዎች ይከተሉ፡\n"
        "1️⃣ መተርጎም የሚፈልጉትን ጽሑፍ ይጻፉልኝ።\n"
        "2️⃣ ከሚመጡት አማራጮች ውስጥ ቋንቋውን ይምረጡ።\n"
        "3️⃣ ትርጉሙን በአፋጣኝ ይጠብቁ! ⚡\n\n"
        "📜 **የትዕዛዝ ዝርዝር:**\n"
        "/start - 🔄 ቦቱን ዳግም ያስጀምሩ\n"
        "/about - ℹ️ ስለ ቦቱ ዝርዝር መረጃ\n"
        "/help - 🆘 የእገዛ ማዕከል\n\n"
        "📌 **ማሳሰቢያ:** ማንኛውም የቴክኒክ ችግር ወይም አስተያየት ካለዎት በ @th\_ug\_life ያግኙን።"
    )
    bot.reply_to(message, help_text, parse_mode='Markdown')

@bot.message_handler(commands=['stats'])
def get_stats(message):
    if message.from_user.id == ADMIN_ID:
        conn = sqlite3.connect('bot_data.db')
        cursor = conn.cursor()
        cursor.execute('SELECT COUNT(*) FROM users')
        count = cursor.fetchone()[0]
        conn.close()
        bot.reply_to(message, f"👥 **የቦቱ ጠቅላላ ተጠቃሚዎች:** `{count}`")
    else:
        bot.reply_to(message, "🚫 ይህ ትዕዛዝ ለአስተዳዳሪ ብቻ የተፈቀደ ነው!")

# --- MESSAGE HANDLER ---

@bot.message_handler(func=lambda message: True)
def handle_text(message):
    if message.text.startswith('/'): return
    user_data[message.chat.id] = message.text
    
    markup = types.InlineKeyboardMarkup(row_width=2)
    buttons = [types.InlineKeyboardButton(f"{info['name']} {info['flag']}", callback_data=code) 
               for code, info in lang_info.items()]
    markup.add(*buttons)
    bot.reply_to(message, "✅ **ጽሁፉን ተቀብያለሁ!**\n\nወደ የትኛው ቋንቋ ልተርጉምልዎ?", reply_markup=markup)

# --- CALLBACK QUERY HANDLER ---

@bot.callback_query_handler(func=lambda call: True)
def callback_query(call):
    chat_id = call.message.chat.id
    target_lang = call.data
    original_text = user_data.get(chat_id)
    
    if not original_text:
        bot.send_message(chat_id, "⚠️ **እባክዎ መጀመሪያ ጽሁፍ ይላኩልኝ።**")
        return

    bot.edit_message_reply_markup(chat_id=chat_id, message_id=call.message.message_id, reply_markup=None)

    try:
        translator = GoogleTranslator(source='auto', target=target_lang)
        translated = translator.translate(original_text)
        lang_flag = lang_info[target_lang]['flag']
        
        result_text = f"{lang_flag} **ትርጉም:**\n\n_{translated}_\n\n━━━━━━━━━━━━━━━━━━\n🤖 @vision_translator_bot"
        bot.send_message(chat_id, result_text, parse_mode='Markdown')
    except Exception:
        bot.send_message(chat_id, "⚠️ **ይቅርታ፣ መተርጎም አልቻልኩም።**")

bot.infinity_polling()

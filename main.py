import os
import sqlite3
import telebot
import pytesseract
from PIL import Image
import io
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
user_states = {} # ለOCR ሁኔታ መቆጣጠሪያ

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
    welcome_text = "✨ **እንኳን ወደ Vision Translator በደህና መጡ!** ✨\n\nጽሑፍ ለመተርጎም በቀጥታ ይላኩልኝ ወይም `/ocr` ብለው ምስል ይላኩ።"
    bot.reply_to(message, welcome_text, parse_mode='Markdown')

@bot.message_handler(commands=['ocr'])
def start_ocr(message):
    user_states[message.chat.id] = 'waiting_for_image'
    bot.reply_to(message, "📸 **እባክዎን ጽሑፍ ያለበትን ምስል ይላኩልኝ።**")

@bot.message_handler(commands=['about'])
def send_about(message):
    bot.reply_to(message, "🤖 **Vision Translator**\n\nፈጣን ትርጉም እና OCR አገልግሎት።\nስሪት: 1.2.0", parse_mode='Markdown')

@bot.message_handler(commands=['help'])
def send_help(message):
    help_text = (
        "💡 **የእገዛ ማዕከል** 🆘\n\n"
        "/start - ቦቱን ለመጀመር\n"
        "/ocr - ምስል ለመተርጎም\n"
        "/help - እገዛ ለማግኘት\n\n"
        "📌 **ማሳሰቢያ:** ማንኛውም ጥያቄ ካለዎት በ @th\_ug\_life ያግኙን።"
    )
    bot.reply_to(message, help_text, parse_mode='Markdown')

# --- IMAGE HANDLER (OCR) ---

@bot.message_handler(content_types=['photo'])
def handle_image(message):
    if user_states.get(message.chat.id) == 'waiting_for_image':
        bot.reply_to(message, "⏳ **ምስሉን እያነበብኩ ነው...**")
        file_id = message.photo[-1].file_id
        file_info = bot.get_file(file_id)
        downloaded_file = bot.download_file(file_info.file_path)
        
        img = Image.open(io.BytesIO(downloaded_file))
        text = pytesseract.image_to_string(img)
        
        if not text.strip():
            bot.reply_to(message, "⚠️ **ጽሑፍ ማግኘት አልቻልኩም።**")
        else:
            user_data[message.chat.id] = text
            show_lang_menu(message, "✅ **የተገኘ ጽሑፍ:**\n\n_" + text + "_\n\nወደ የትኛው ቋንቋ ልተርጉምልዎ?")
        user_states[message.chat.id] = None
    else:
        bot.reply_to(message, "⚠️ ምስል ለመተርጎም መጀመሪያ `/ocr` ብለው ይላኩ።")

# --- TEXT HANDLER ---

@bot.message_handler(func=lambda message: True)
def handle_text(message):
    if message.text.startswith('/'): return
    user_data[message.chat.id] = message.text
    show_lang_menu(message, "✅ **ጽሁፉን ተቀብያለሁ!**\n\nወደ የትኛው ቋንቋ ልተርጉምልዎ?")

def show_lang_menu(message, text):
    markup = types.InlineKeyboardMarkup(row_width=2)
    buttons = [types.InlineKeyboardButton(f"{info['name']} {info['flag']}", callback_data=code) 
               for code, info in lang_info.items()]
    markup.add(*buttons)
    bot.reply_to(message, text, reply_markup=markup, parse_mode='Markdown')

# --- CALLBACK ---

@bot.callback_query_handler(func=lambda call: True)
def callback_query(call):
    chat_id = call.message.chat.id
    target_lang = call.data
    original_text = user_data.get(chat_id)
    
    if not original_text:
        bot.send_message(chat_id, "⚠️ **እባክዎ መጀመሪያ ጽሁፍ ወይም ምስል ይላኩ።**")
        return

    bot.edit_message_reply_markup(chat_id=chat_id, message_id=call.message.message_id, reply_markup=None)
    try:
        translated = GoogleTranslator(source='auto', target=target_lang).translate(original_text)
        lang_flag = lang_info[target_lang]['flag']
        bot.send_message(chat_id, f"{lang_flag} **ትርጉም:**\n\n_{translated}_\n\n━━━━━━━━━━━━━━━━━━\n🤖 @vision_translator_bot", parse_mode='Markdown')
    except:
        bot.send_message(chat_id, "⚠️ **ይቅርታ፣ ስህተት ተፈጥሯል።**")

bot.infinity_polling()

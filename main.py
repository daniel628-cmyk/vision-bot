import os
import sqlite3
import telebot
import pytesseract
from PIL import Image
import io
from deep_translator import GoogleTranslator
from telebot import types

# Tesseract path (ለLinux ሰርቨሮች አስፈላጊ ነው)
pytesseract.pytesseract.tesseract_cmd = '/usr/bin/tesseract'

TOKEN = os.environ.get('BOT_TOKEN')
bot = telebot.TeleBot(TOKEN)

# የቦቱን ሁኔታ እና መረጃ ለመያዝ
user_data = {}
user_states = {} 

lang_info = {
    "am": {"name": "አማርኛ", "flag": "🇪🇹"},
    "en": {"name": "English", "flag": "🇺🇸"},
    "om": {"name": "Oromiffa", "flag": "🌳"},
    "ar": {"name": "العربية", "flag": "🇸🇦"}
}

# --- COMMANDS ---

@bot.message_handler(commands=['start'])
def send_welcome(message):
    welcome_text = (
        "✨ **ሰላም! ወደ Vision AI Translator & OCR Bot በደህና መጡ!** ✨\n\n"
        "ምን ማድረግ እችላለሁ? 👇\n"
        "📝 **ጽሑፍ ለመተርጎም** - በቀጥታ ጽሁፉን ይላኩልኝ።\n"
        "📸 **ምስልን ወደ ጽሑፍ ለመቀየር** - `/ocr` ብለው ይላኩልኝ።\n\n"
        "💡 *የእገዛ ዝርዝር ለማግኘት* `/help` ይጠቀሙ።"
    )
    bot.reply_to(message, welcome_text, parse_mode='Markdown')

@bot.message_handler(commands=['ocr'])
def start_ocr(message):
    user_states[message.chat.id] = 'waiting_for_image'
    bot.reply_to(message, "📸 **እሺ! ምስሉን ይላኩልኝ፣ ወደ ጽሑፍ እቀይርልዎታለሁ።**")

@bot.message_handler(commands=['help'])
def send_help(message):
    help_text = (
        "🆘 **የእገዛ ማዕከል** 🆘\n\n"
        "🔄 `/start` - ቦቱን ዳግም ያስጀምሩ\n"
        "📸 `/ocr` - ምስልን ወደ ጽሑፍ ይቀይሩ\n"
        "ℹ️ `/about` - ስለ ቦቱ መረጃ\n\n"
        "📌 *ለአስተያየት* 💬 በ @th\_ug\_life ያግኙን።"
    )
    bot.reply_to(message, help_text, parse_mode='Markdown')

# --- HANDLERS ---

@bot.message_handler(content_types=['photo'])
def handle_image(message):
    if user_states.get(message.chat.id) == 'waiting_for_image':
        bot.reply_to(message, "⏳ **እባክዎ ትንሽ ይጠብቁ፣ ምስሉን እያነበብኩ ነው...**")
        
        file_id = message.photo[-1].file_id
        file_info = bot.get_file(file_id)
        downloaded_file = bot.download_file(file_info.file_path)
        
        img = Image.open(io.BytesIO(downloaded_file)).convert('L')
        text = pytesseract.image_to_string(img)
        
        if not text.strip():
            bot.reply_to(message, "⚠️ **ይቅርታ፣ ምስሉ ላይ ጽሑፍ አላገኘሁም።**")
        else:
            bot.reply_to(message, f"✅ **የተገኘው ጽሑፍ:**\n\n`{text}`", parse_mode='Markdown')
        
        user_states[message.chat.id] = None # ሁኔታውን እንደገና ወደ መደበኛ መለስነው
    else:
        bot.reply_to(message, "⚠️ **ምስል ለመቀየር መጀመሪያ `/ocr` ብለው ይላኩ።**")

@bot.message_handler(func=lambda message: True)
def handle_text(message):
    # ትዕዛዝ ካልሆነ ብቻ ወደ ትርጉም ይሂድ
    if message.text.startswith('/'): return
    
    user_data[message.chat.id] = message.text
    
    markup = types.InlineKeyboardMarkup(row_width=2)
    buttons = [types.InlineKeyboardButton(f"{info['name']} {info['flag']}", callback_data=code) 
               for code, info in lang_info.items()]
    markup.add(*buttons)
    bot.reply_to(message, "✅ **ጽሁፉን ተቀብያለሁ!**\n\nወደ የትኛው ቋንቋ ልተርጉምልዎ?", reply_markup=markup)

@bot.callback_query_handler(func=lambda call: True)
def callback_query(call):
    chat_id = call.message.chat.id
    target_lang = call.data
    original_text = user_data.get(chat_id)
    
    if original_text:
        translated = GoogleTranslator(source='auto', target=target_lang).translate(original_text)
        bot.send_message(chat_id, f"🌍 **ትርጉም:**\n\n_{translated}_", parse_mode='Markdown')
    else:
        bot.send_message(chat_id, "⚠️ **እባክዎ መጀመሪያ ጽሁፍ ይላኩ።**")

bot.infinity_polling()

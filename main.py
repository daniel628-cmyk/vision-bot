import os
import sqlite3
import telebot
import pytesseract
from PIL import Image
import io

# Tesseract ትክክለኛ ቦታ (Linux ሰርቨሮች ላይ)
pytesseract.pytesseract.tesseract_cmd = '/usr/bin/tesseract'

TOKEN = os.environ.get('BOT_TOKEN')
bot = telebot.TeleBot(TOKEN)

# የOCR ሁኔታን ለመያዝ
user_states = {}

def init_db():
    conn = sqlite3.connect('bot_data.db')
    cursor = conn.cursor()
    cursor.execute('CREATE TABLE IF NOT EXISTS users (user_id INTEGER PRIMARY KEY)')
    conn.commit()
    conn.close()

init_db()

# --- COMMAND HANDLERS ---

@bot.message_handler(commands=['start'])
def send_welcome(message):
    conn = sqlite3.connect('bot_data.db')
    cursor = conn.cursor()
    cursor.execute('INSERT OR IGNORE INTO users (user_id) VALUES (?)', (message.from_user.id,))
    conn.commit()
    conn.close()
    welcome_text = "✨ **እንኳን ወደ Image to Text ቦት በደህና መጡ!** ✨\n\nምስልን ወደ ጽሑፍ ለመቀየር `/ocr` ብለው ይላኩ።"
    bot.reply_to(message, welcome_text, parse_mode='Markdown')

@bot.message_handler(commands=['ocr'])
def start_ocr(message):
    user_states[message.chat.id] = 'waiting_for_image'
    bot.reply_to(message, "📸 **እባክዎን ጽሑፍ ያለበትን ምስል ይላኩልኝ።**")

@bot.message_handler(commands=['about'])
def send_about(message):
    bot.reply_to(message, "🤖 **Vision Text Bot**\n\nምስልን ወደ ጽሑፍ የመቀየር አገልግሎት።", parse_mode='Markdown')

@bot.message_handler(commands=['help'])
def send_help(message):
    help_text = (
        "💡 **የእገዛ ማዕከል** 🆘\n\n"
        "/start - ቦቱን ለመጀመር\n"
        "/ocr - ምስል ወደ ጽሑፍ ለመቀየር\n"
        "/help - እገዛ ለማግኘት\n\n"
        "📌 **ማሳሰቢያ:** ማንኛውም የቴክኒክ ችግር ካለዎት በ @th\_ug\_life ያግኙን።"
    )
    bot.reply_to(message, help_text, parse_mode='Markdown')

# --- IMAGE HANDLER (OCR ONLY) ---

@bot.message_handler(content_types=['photo'])
def handle_image(message):
    if user_states.get(message.chat.id) == 'waiting_for_image':
        try:
            bot.reply_to(message, "⏳ **ምስሉን እያነበብኩ ነው፣ ትንሽ ይጠብቁ...**")
            
            # ምስሉን ማውረድ
            file_id = message.photo[-1].file_id
            file_info = bot.get_file(file_id)
            downloaded_file = bot.download_file(file_info.file_path)
            
            # ምስሉን ወደ ግራጫ መቀየር እና ጽሑፍ ማንበብ
            img = Image.open(io.BytesIO(downloaded_file)).convert('L')
            text = pytesseract.image_to_string(img)
            
            if not text.strip():
                bot.reply_to(message, "⚠️ **ይቅርታ፣ ምስሉ ላይ ግልጽ ጽሑፍ ማግኘት አልቻልኩም።**")
            else:
                # ጽሑፉን ብቻ ነው የምንልከው
                bot.reply_to(message, f"✅ **በምስሉ ላይ የተገኘው ጽሑፍ:**\n\n`{text}`", parse_mode='Markdown')
            
            user_states[message.chat.id] = None
        except Exception as e:
            bot.reply_to(message, f"⚠️ **ስህተት ተፈጥሯል:** {str(e)}")
            user_states[message.chat.id] = None
    else:
        bot.reply_to(message, "⚠️ **ምስል ወደ ጽሑፍ ለመቀየር መጀመሪያ `/ocr` ብለው ይላኩ።**")

# ለሌሎች ጽሁፎች መልስ
@bot.message_handler(func=lambda message: True)
def handle_other(message):
    if message.text.startswith('/'): return
    bot.reply_to(message, "እባክዎን ምስል ለመላክ `/ocr` የሚለውን ትዕዛዝ ይጠቀሙ።")

bot.infinity_polling()

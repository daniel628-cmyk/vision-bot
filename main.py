import os
import sqlite3
import telebot
from telebot import types
import pytesseract
from PIL import Image
import io
from deep_translator import GoogleTranslator

# --- Tesseract Configuration ---
pytesseract.pytesseract.tesseract_cmd = '/usr/bin/tesseract'

TOKEN = os.environ.get('BOT_TOKEN')
bot = telebot.TeleBot(TOKEN)

# የአንተ User ID (ለ /stats)
ADMIN_ID = 5544893200

# --- Database Setup (ለ Stats) ---
conn = sqlite3.connect('users.db', check_same_thread=False)
cursor = conn.cursor()
cursor.execute('''CREATE TABLE IF NOT EXISTS users (user_id INTEGER PRIMARY KEY)''')
conn.commit()

def add_user(user_id):
    cursor.execute('INSERT OR IGNORE INTO users (user_id) VALUES (?)', (user_id,))
    conn.commit()

# --- State Trackers ---
user_states = {}
user_texts = {} # ለማስተርጎም የተላከውን ጽሑፍ ለመያዝ

# 2. የቋንቋዎች ዝርዝር (በምስሉ ላይ እንዳለው)
LANGUAGES = [
    ("Amharic 🇪🇹", "am"), ("Oromo 🟢", "om"),
    ("Somali 🔵", "so"), ("Tigrinya 🟡", "ti"),
    ("English 🇬🇧", "en"), ("Arabic 🇸🇦", "ar"),
    ("French 🇫🇷", "fr"), ("German 🇩🇪", "de"),
    ("Spanish 🇪🇸", "es"), ("Portuguese 🇵🇹", "pt"),
    ("Italian 🇮🇹", "it"), ("Russian 🇷🇺", "ru")
]

# --- 4. Start Command & Welcome Message ---
@bot.message_handler(commands=['start'])
def send_welcome(message):
    add_user(message.chat.id)
    user_name = message.from_user.first_name
    
    # ልክ እንደጠየቅከው ያማረ የሰላምታ መልእክት
    welcome_text = (
        f"🌟 👋 **{user_name}** እንኳን በደህና መጡ!! 🌟\n\n"
        "ይህ ቦት ሁለት ጠቃሚ ነገሮች ያደርግልዎታል፦\n"
        "1️⃣ ጽሁፍ በቋንቋ መቀየር (ትርጉም)\n"
        "2️⃣ ከምስል ጽሁፍ መውጣት (OCR)\n\n"
        "📝 <b>**ትርጉም ለማድረግ :** </b>\n"
        "<blockquote> ➻ የሚፈልጉትን ጽሁፍ ይላኩ ከዛን ከስር ቋንቋ ይምረጡ ።\n"
        " ➻ ምስል ለመቀየር OCR የሚለውን ይንኩት ከዛን ምስል ይላኩ ።</blockquote>"
    )
    
    # የቻናል፣ ክሬተር እና OCR ቁልፎች
    markup = types.InlineKeyboardMarkup(row_width=2)
    btn1 = types.InlineKeyboardButton("📺 Our Channel", url="https://t.me/ethio_vision_tools")
    btn2 = types.InlineKeyboardButton("👨‍💻 Creator", url="https://t.me/th_ug_life")
    btn_ocr = types.InlineKeyboardButton("📸 OCR (Image to Text)", callback_data="start_ocr")
    
    markup.add(btn1, btn2)
    markup.add(btn_ocr)
    
    bot.send_message(message.chat.id, welcome_text, parse_mode='Markdown', reply_markup=markup)

# --- 3. Stats, About & Help Commands ---
@bot.message_handler(commands=['about'])
def about_command(message):
    add_user(message.chat.id)
    about_text = (
        "ℹ️ **ስለ ቦቱ (About Us)** ℹ️\n\n"
        "🤖 **Vision Translate Bot ** የተሰራው የእለት ተእለት የትርጉም እና የጽሑፍ ልወጣ ስራዎችን ለማቃለል ነው።\n\n"
        "✨ **ዋና ዋና አገልግሎቶቻችን:**\n"
        "🔹 ትክክለኛ የጽሑፍ ትርጉም (በተለያዩ ቋንቋዎች)\n"
        "🔹 ምስልን ወደ ጽሑፍ መቀየር (OCR Technology)\n\n"
        "👨‍💻 **አዘጋጅ:** [@th\\_ug\\_life](https://t.me/th_ug_life)\n"
        "📢 **ቻናላችን:** [@ethio\\_vision\\_tools](https://t.me/ethio_vision_tools)\n\n"
        "💡 _ማንኛውም አስተያየት ወይም ጥያቄ ካሎት አዘጋጁን ማነጋገር ይችላሉ!_"
    )
    bot.send_message(message.chat.id, about_text, parse_mode="Markdown", disable_web_page_preview=True)

@bot.message_handler(commands=['help'])
def help_command(message):
    add_user(message.chat.id)
    help_text = (
        "🆘 **የእገዛ ማዕከል (Help Center)** 🆘\n\n"
        "ቦቱን እንዴት መጠቀም እንደሚችሉ መመሪያዎች፦\n\n"
        "1️⃣ **ትርጉም (Translation):**\n"
        "➻ በቀጥታ መተርጎም የሚፈልጉትን ጽሑፍ ይጻፉልኝ።\n"
        "➻ ጽሑፉን እንደላኩ የቋንቋ መምረጫ አቀርብልዎታለሁ፣ ቋንቋውን ሲመርጡ ወዲያውኑ ይተረጎማል።\n\n"
        "2️⃣ **ምስል ወደ ጽሑፍ (OCR):**\n"
        "➻ መጀመሪያ `/start` ብለው የ **📸 OCR** ቁልፍን ይጫኑ።\n"
        "➻ በመቀጠል ጽሑፍ ያለበትን ምስል ይላኩልኝ።\n\n"
        "🔄 `/start` - ቦቱን አዲስ ለማስጀመር\n"
       " 💠 ' /OCR ' - ምስል ወደ ፅሁፍ ለመቀየር"
        "ℹ️ `/about` - ስለ ቦቱ ለማወቅ"
    )
    bot.send_message(message.chat.id, help_text, parse_mode="Markdown")

@bot.message_handler(commands=['stats'])
def stats_command(message):
    add_user(message.chat.id)
    # አንተ ብቻ (Admin) እንድታየው ማረጋገጫ
    if message.chat.id == ADMIN_ID:
        cursor.execute('SELECT COUNT(*) FROM users')
        count = cursor.fetchone()[0]
        stats_text = (
            "📊 **የቦት የስታትስቲክስ መረጃ (Bot Stats)** 📊\n\n"
            f"👥 **አጠቃላይ ተጠቃሚዎች:** `{count}`\n\n"
            "📈 _ይህ መረጃ የሚታየው ለዋናው አድሚን (Creator) ብቻ ነው።_"
        )
        bot.send_message(message.chat.id, stats_text, parse_mode="Markdown")
    else:
        bot.send_message(message.chat.id, "⚠️ **ይቅርታ! ይህን ትዕዛዝ መጠቀም የሚችለው የቦቱ ባለቤት (Admin) ብቻ ነው።**", parse_mode="Markdown")

# --- 1. OCR (Image Handler) የተሻሻለ ---
@bot.callback_query_handler(func=lambda call: call.data == "start_ocr")
def ocr_callback(call):
    user_states[call.message.chat.id] = 'waiting_for_image'
    bot.answer_callback_query(call.id)
    bot.send_message(call.message.chat.id, "📸 **እሺ! ጽሑፍ ያለበትን ምስል አሁን ይላኩልኝ...**")

@bot.message_handler(content_types=['photo'])
def handle_image(message):
    add_user(message.chat.id)
    if user_states.get(message.chat.id) == 'waiting_for_image':
        msg = bot.reply_to(message, "⏳ **ምስሉን በማንበብ ላይ ነኝ፣ እባክዎ ትንሽ ይጠብቁ...**\n_(ምስሉ ግልጽ መሆኑ ውጤቱን የተሻለ ያደርገዋል)_")
        try:
            file_info = bot.get_file(message.photo[-1].file_id)
            downloaded_file = bot.download_file(file_info.file_path)
            
            # ምስሉን ወደ ጥቁርና ነጭ (Grayscale) መቀየር OCR በተሻለ እንዲያነብ ይረዳል
            img = Image.open(io.BytesIO(downloaded_file)).convert('L') 
            
            text = pytesseract.image_to_string(img)
            
            if text.strip():
                bot.edit_message_text(f"✅ **የተገኘ ጽሑፍ (OCR Result):**\n\n`{text}`", chat_id=message.chat.id, message_id=msg.message_id, parse_mode='Markdown')
            else:
                bot.edit_message_text("⚠️ **ይቅርታ፣ ከምስሉ ላይ ምንም ግልጽ ጽሑፍ ማግኘት አልቻልኩም። እባክዎ ጥራት ያለው ምስል ይላኩ።**", chat_id=message.chat.id, message_id=msg.message_id)
        except Exception as e:
            bot.edit_message_text("❌ **ምስሉን በማንበብ ጊዜ የቴክኒክ ስህተት ተፈጥሯል።**", chat_id=message.chat.id, message_id=msg.message_id)
            print(f"OCR Error: {e}")
        
        user_states[message.chat.id] = None
    else:
        bot.reply_to(message, "⚠️ **ምስል ወደ ጽሑፍ ለመቀየር መጀመሪያ `/start` ብለው '📸 OCR' የሚለውን ቁልፍ ይጫኑ።**")

# --- Translation Handler & Language Keyboard ---
@bot.message_handler(func=lambda message: True)
def handle_text(message):
    add_user(message.chat.id)
    if message.text.startswith('/'): return
    
    # ጽሑፉን ለጊዜው እናስቀምጠዋለን
    user_texts[message.chat.id] = message.text
    
    # የቋንቋ መምረጫ ቁልፎች (ልክ እንደ ላክኸው ምስል 3)
    markup = types.InlineKeyboardMarkup(row_width=2)
    buttons = [types.InlineKeyboardButton(name, callback_data=f"lang_{code}") for name, code in LANGUAGES]
    markup.add(*buttons)
    
    bot.reply_to(message, "👇 **Select your target language (የሚፈልጉትን ቋንቋ ይምረጡ):**", reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data.startswith("lang_"))
def lang_callback(call):
    chat_id = call.message.chat.id
    target_lang = call.data.split("_")[1]
    original_text = user_texts.get(chat_id)
    
    if not original_text:
        bot.answer_callback_query(call.id, "⚠️ ጽሑፉ ተሰርዟል፣ እባክዎ እንደገና ይላኩ።")
        return
        
    bot.answer_callback_query(call.id, "እየተረጎምኩ ነው...")
    bot.edit_message_text("⏳ **እየተረጎምኩ ነው (Translating)...**", chat_id=chat_id, message_id=call.message.message_id)
    
    try:
        translated = GoogleTranslator(source='auto', target=target_lang).translate(original_text)
        # የመረጠውን ቋንቋ ስም መፈለግ
        lang_name = next(name for name, code in LANGUAGES if code == target_lang)
        
        result_text = f"🌍 **ትርጉም ({lang_name}):**\n\n`{translated}`"
        bot.edit_message_text(result_text, chat_id=chat_id, message_id=call.message.message_id, parse_mode='Markdown')
    except Exception as e:
        bot.edit_message_text("❌ **ይቅርታ! ጽሑፉን መተርጎም አልተቻለም።**", chat_id=chat_id, message_id=call.message.message_id)
        print(f"Translation Error: {e}")

if __name__ == '__main__':
    print("Bot is running...")
    bot.infinity_polling(timeout=60, long_polling_timeout=60)

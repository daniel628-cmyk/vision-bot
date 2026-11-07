import os
import io
import sqlite3
import traceback

import telebot
from telebot import types
import pytesseract
from PIL import Image
from deep_translator import GoogleTranslator

# --- Tesseract Configuration ---
pytesseract.pytesseract.tesseract_cmd = '/usr/bin/tesseract'

TOKEN = os.environ.get('BOT_TOKEN')
if not TOKEN:
    raise RuntimeError('BOT_TOKEN environment variable is missing. Set it in your hosting dashboard.')

bot = telebot.TeleBot(TOKEN)

# Admin user ID for /stats
ADMIN_ID = 5544893200

# --- Database Setup ---
conn = sqlite3.connect('users.db', check_same_thread=False)
cursor = conn.cursor()
cursor.execute('CREATE TABLE IF NOT EXISTS users (user_id INTEGER PRIMARY KEY)')
conn.commit()


def add_user(user_id):
    cursor.execute('INSERT OR IGNORE INTO users (user_id) VALUES (?)', (user_id,))
    conn.commit()


# --- State Trackers ---
user_states = {}
user_texts = {}

LANGUAGES = [
    ("Amharic 🇪🇹", "am"), ("Oromo 🟢", "om"),
    ("Somali 🔵", "so"), ("Tigrinya 🟡", "ti"),
    ("English 🇬🇧", "en"), ("Arabic 🇸🇦", "ar"),
    ("French 🇫🇷", "fr"), ("German 🇩🇪", "de"),
    ("Spanish 🇪🇸", "es"), ("Portuguese 🇵🇹", "pt"),
    ("Italian 🇮🇹", "it"), ("Russian 🇷🇺", "ru")
]


def split_text(text, limit=4500):
    """Split long input into chunks suitable for deep-translator."""
    chunks = []
    remaining = text.strip()
    while remaining:
        if len(remaining) <= limit:
            chunks.append(remaining)
            break
        cut = remaining.rfind('\n', 0, limit)
        if cut < limit // 2:
            cut = remaining.rfind(' ', 0, limit)
        if cut < limit // 2:
            cut = limit
        chunks.append(remaining[:cut].strip())
        remaining = remaining[cut:].strip()
    return [chunk for chunk in chunks if chunk]


def split_telegram_text(text, limit=4000):
    """Split output below Telegram's 4096-character message limit."""
    parts = []
    remaining = text
    while len(remaining) > limit:
        cut = remaining.rfind('\n', 0, limit)
        if cut < limit // 2:
            cut = remaining.rfind(' ', 0, limit)
        if cut < limit // 2:
            cut = limit
        parts.append(remaining[:cut].strip())
        remaining = remaining[cut:].strip()
    if remaining:
        parts.append(remaining)
    return parts


# --- Start Command & Welcome Message ---
@bot.message_handler(commands=['start'])
def send_welcome(message):
    add_user(message.chat.id)
    user_name = message.from_user.first_name or 'there'
    welcome_text = (
        f"🌟 👋 {user_name} እንኳን በደህና መጡ!! 🌟\n\n"
        "ይህ ቦት ሁለት ጠቃሚ ነገሮች ያደርግልዎታል፦\n"
        "1️⃣ ጽሁፍ በቋንቋ መቀየር (ትርጉም)\n"
        "2️⃣ ከምስል ጽሁፍ መውጣት (OCR)\n\n"
        "📝 ትርጉም ለማድረግ:\n"
        "➻ የሚፈልጉትን ጽሑፍ ይላኩ፤ ከዚያ ከስር ቋንቋ ይምረጡ።\n"
        "➻ ምስል ለመቀየር OCR የሚለውን ይጫኑ፤ ከዚያ ምስል ይላኩ።"
    )

    markup = types.InlineKeyboardMarkup(row_width=2)
    btn1 = types.InlineKeyboardButton("📺 Our Channel", url="https://t.me/ethio_vision_tools")
    btn2 = types.InlineKeyboardButton("👨‍💻 Creator", url="https://t.me/th_ug_life")
    btn_ocr = types.InlineKeyboardButton("📸 OCR (Image to Text)", callback_data="start_ocr")
    markup.add(btn1, btn2)
    markup.add(btn_ocr)
    bot.send_message(message.chat.id, welcome_text, reply_markup=markup)


# --- About, Help & Stats Commands ---
@bot.message_handler(commands=['about'])
def about_command(message):
    add_user(message.chat.id)
    about_text = (
        "ℹ️ ስለ ቦቱ (About Us)\n\n"
        "🤖 Vision Translator Bot የእለት ተእለት የትርጉም እና የጽሑፍ ልወጣ ስራዎችን ለማቃለል ነው።\n\n"
        "✨ ዋና ዋና አገልግሎቶቻችን:\n"
        "🔹 በተለያዩ ቋንቋዎች የጽሑፍ ትርጉም\n"
        "🔹 ምስልን ወደ ጽሑፍ መቀየር (OCR)\n\n"
        "👨‍💻 አዘጋጅ: @th_ug_life\n"
        "📢 ቻናል: @ethio_vision_tools\n\n"
        "💡 አስተያየት ወይም ጥያቄ ካሎት አዘጋጁን ማነጋገር ይችላሉ!"
    )
    bot.send_message(message.chat.id, about_text, disable_web_page_preview=True)


@bot.message_handler(commands=['help'])
def help_command(message):
    add_user(message.chat.id)
    help_text = (
        "🆘 የእገዛ ማዕከል (Help Center)\n\n"
        "ቦቱን እንዴት መጠቀም እንደሚችሉ:\n\n"
        "1️⃣ ትርጉም (Translation):\n"
        "➻ መተርጎም የሚፈልጉትን ጽሑፍ ይላኩ።\n"
        "➻ የቋንቋ መምረጫ ይመጣል፤ ቋንቋ ሲመርጡ ይተረጎማል።\n\n"
        "2️⃣ ምስል ወደ ጽሑፍ (OCR):\n"
        "➻ /start ብለው 📸 OCR ቁልፍን ይጫኑ።\n"
        "➻ ጽሑፍ ያለበትን ምስል ይላኩ።\n\n"
        "/start - ቦቱን ለማስጀመር\n"
        "/about - ስለ ቦቱ ለማወቅ\n"
        "/stats - የተጠቃሚዎች ቁጥር (Admin ብቻ)"
    )
    bot.send_message(message.chat.id, help_text)


@bot.message_handler(commands=['stats'])
def stats_command(message):
    add_user(message.chat.id)
    if message.chat.id == ADMIN_ID:
        cursor.execute('SELECT COUNT(*) FROM users')
        count = cursor.fetchone()[0]
        stats_text = (
            "📊 የቦት ስታትስቲክስ (Bot Stats)\n\n"
            f"👥 አጠቃላይ ተጠቃሚዎች: {count}\n\n"
            "📈 ይህ መረጃ ለAdmin ብቻ ነው።"
        )
        bot.send_message(message.chat.id, stats_text)
    else:
        bot.send_message(message.chat.id, "⚠️ ይቅርታ! ይህን ትዕዛዝ መጠቀም የሚችለው Admin ብቻ ነው።")


# --- OCR ---
@bot.callback_query_handler(func=lambda call: call.data == "start_ocr")
def ocr_callback(call):
    user_states[call.message.chat.id] = 'waiting_for_image'
    bot.answer_callback_query(call.id)
    bot.send_message(call.message.chat.id, "📸 እሺ! ጽሑፍ ያለበትን ምስል አሁን ይላኩልኝ...")


@bot.message_handler(content_types=['photo'])
def handle_image(message):
    add_user(message.chat.id)
    if user_states.get(message.chat.id) != 'waiting_for_image':
        bot.reply_to(message, "⚠️ ምስልን ወደ ጽሑፍ ለመቀየር /start ብለው 📸 OCR ቁልፍን ይጫኑ።")
        return

    msg = bot.reply_to(message, "⏳ ምስሉን በማንበብ ላይ ነኝ፣ እባክዎ ይጠብቁ...")
    try:
        file_info = bot.get_file(message.photo[-1].file_id)
        downloaded_file = bot.download_file(file_info.file_path)
        img = Image.open(io.BytesIO(downloaded_file)).convert('L')
        extracted_text = pytesseract.image_to_string(img).strip()

        if extracted_text:
            parts = split_telegram_text("✅ የተገኘ ጽሑፍ (OCR Result):\n\n" + extracted_text)
            bot.edit_message_text(parts[0], chat_id=message.chat.id, message_id=msg.message_id)
            for part in parts[1:]:
                bot.send_message(message.chat.id, part)
        else:
            bot.edit_message_text("⚠️ ከምስሉ ላይ ግልጽ ጽሑፍ ማግኘት አልቻልኩም። እባክዎ ጥራት ያለው ምስል ይላኩ።", chat_id=message.chat.id, message_id=msg.message_id)
    except Exception:
        print('OCR ERROR:')
        traceback.print_exc()
        bot.edit_message_text("❌ ምስሉን በማንበብ ጊዜ የቴክኒክ ስህተት ተፈጥሯል።", chat_id=message.chat.id, message_id=msg.message_id)
    finally:
        user_states[message.chat.id] = None


# --- Text Translation Handler ---
@bot.message_handler(func=lambda message: bool(message.text))
def handle_text(message):
    add_user(message.chat.id)
    if message.text.startswith('/'):
        return

    user_texts[message.chat.id] = message.text
    markup = types.InlineKeyboardMarkup(row_width=2)
    buttons = [types.InlineKeyboardButton(name, callback_data=f"lang_{code}") for name, code in LANGUAGES]
    markup.add(*buttons)
    bot.reply_to(message, "👇 Select your target language (የሚፈልጉትን ቋንቋ ይምረጡ):", reply_markup=markup)


@bot.callback_query_handler(func=lambda call: call.data.startswith("lang_"))
def lang_callback(call):
    chat_id = call.message.chat.id
    target_lang = call.data.split("_", 1)[1]
    original_text = user_texts.get(chat_id)

    if not original_text:
        bot.answer_callback_query(call.id, "⚠️ ጽሑፉ አልተገኘም፤ እባክዎ እንደገና ይላኩ።")
        return

    bot.answer_callback_query(call.id, "እየተረጎምኩ ነው...")
    bot.edit_message_text("⏳ እየተረጎምኩ ነው (Translating)...", chat_id=chat_id, message_id=call.message.message_id)

    try:
        source_chunks = split_text(original_text)
        translated_chunks = []
        translator = GoogleTranslator(source='auto', target=target_lang)
        for chunk in source_chunks:
            translated_part = translator.translate(chunk)
            if translated_part is None:
                raise RuntimeError('GoogleTranslator returned an empty result.')
            translated_chunks.append(translated_part)

        lang_name = next((name for name, code in LANGUAGES if code == target_lang), target_lang)
        result = f"🌍 ትርጉም ({lang_name}):\n\n" + "\n".join(translated_chunks)
        output_parts = split_telegram_text(result)
        bot.edit_message_text(output_parts[0], chat_id=chat_id, message_id=call.message.message_id)
        for part in output_parts[1:]:
            bot.send_message(chat_id, part)
    except Exception:
        print('TRANSLATION ERROR:')
        traceback.print_exc()
        try:
            bot.edit_message_text("❌ ይቅርታ! ጽሑፉን መተርጎም አልተቻለም። እባክዎ ቆይተው እንደገና ይሞክሩ።", chat_id=chat_id, message_id=call.message.message_id)
        except Exception:
            traceback.print_exc()


if __name__ == '__main__':
    print('Vision Translator Bot is starting...')
    bot.infinity_polling(timeout=60, long_polling_timeout=60)

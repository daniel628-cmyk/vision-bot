import os
import telebot
from deep_translator import GoogleTranslator
from telebot import types

TOKEN = os.environ.get('BOT_TOKEN')
if not TOKEN:
    exit("ስህተት: BOT_TOKEN በ Railway Variables ውስጥ አልተገኘም!")

bot = telebot.TeleBot(TOKEN)

user_data = {}

# ቋንቋ እና ምልክታቸው
lang_info = {
    "am": {"name": "አማርኛ", "flag": "🇪🇹"},
    "en": {"name": "English", "flag": "🇺🇸"},
    "om": {"name": "Oromiffa", "flag": "🌳"},
    "es": {"name": "Español", "flag": "🇪🇸"},
    "fr": {"name": "Français", "flag": "🇫🇷"},
    "ar": {"name": "العربية", "flag": "🇸🇦"},
    "de": {"name": "Deutsch", "flag": "🇩🇪"}
}

@bot.message_handler(commands=['start'])
def send_welcome(message):
    user_name = message.from_user.first_name
    welcome_text = (
        f"✨ **ሰላም {user_name}! ወደ Vision Translator እንኳን በደህና መጡ!** ✨\n\n"
        "ጽሑፎችን በቀላሉ ወደፈለጉት ቋንቋ ለመተርጎም እዚህ ነኝ። 🌍\n\n"
        "🚀 **ለመጀመር:** መተርጎም የሚፈልጉትን ጽሑፍ ይላኩልኝ።"
    )
    bot.reply_to(message, welcome_text, parse_mode='Markdown')

@bot.message_handler(func=lambda message: True)
def handle_text(message):
    if message.text.startswith('/'): return
    user_data[message.chat.id] = message.text
    
    markup = types.InlineKeyboardMarkup(row_width=2)
    buttons = [types.InlineKeyboardButton(f"{info['name']} {info['flag']}", callback_data=code) 
               for code, info in lang_info.items()]
    markup.add(*buttons)
    
    bot.reply_to(message, "✅ ጽሁፉን ተቀብያለሁ! ወደ የትኛው ቋንቋ ልተርጉምልዎ?", reply_markup=markup)

@bot.callback_query_handler(func=lambda call: True)
def callback_query(call):
    chat_id = call.message.chat.id
    target_lang = call.data
    original_text = user_data.get(chat_id)
    
    if not original_text:
        bot.send_message(chat_id, "⚠️ እባክዎ መጀመሪያ ጽሁፍ ይላኩልኝ።")
        return

    bot.edit_message_reply_markup(chat_id=chat_id, message_id=call.message.message_id, reply_markup=None)

    try:
        translator = GoogleTranslator(source='auto', target=target_lang)
        if len(original_text) > 2000:
            part1 = original_text[:2000]
            part2 = original_text[2000:]
            translated = translator.translate(part1) + "\n\n" + translator.translate(part2)
        else:
            translated = translator.translate(original_text)
            
        # የተመረጠው ቋንቋ ምልክት
        lang_flag = lang_info[target_lang]['flag']
        
        result_text = f"{lang_flag} **ትርጉም:**\n\n{translated}\n\n━━━━━━━━━━━━━━━━━━\n🤖 @vision_translator_bot"
        bot.send_message(chat_id, result_text, parse_mode='Markdown')
        
    except Exception:
        bot.send_message(chat_id, "⚠️ ይቅርታ፣ መተርጎም አልቻልኩም።")

bot.infinity_polling()

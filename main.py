import os
import telebot
from deep_translator import GoogleTranslator
from telebot import types

# ቶከን ከ Railway Variables ይወስዳል
TOKEN = os.environ.get('BOT_TOKEN')
if not TOKEN:
    exit("ስህተት: BOT_TOKEN በ Railway Variables ውስጥ አልተገኘም!")

bot = telebot.TeleBot(TOKEN)

user_data = {}

# የቋንቋዎች ዝርዝር
lang_info = {
    "am": "አማርኛ 🇪🇹", 
    "en": "English 🇺🇸", 
    "om": "Oromiffa 🌳", 
    "es": "Español 🇪🇸", 
    "fr": "Français 🇫🇷",
    "ar": "العربية 🇸🇦",
    "de": "Deutsch 🇩🇪"
}

@bot.message_handler(commands=['start'])
def send_welcome(message):
    user_name = message.from_user.first_name
    welcome_text = (
        f"✨ **እንኳን ወደ Vision Translator Bot በደህና መጡ!** ✨\n\n"
        f"ሰላም {user_name}! 👋\n"
        "ከአንድ ቋንቋ ወደ ሌላ ቋንቋ ትክክለኛ እና ፈጣን ትርጉም ለማግኘት እዚህ ነኝ። 🌍\n\n"
        "🚀 **እንዴት መጠቀም ይቻላል?**\n"
        "መተርጎም የሚፈልጉትን ጽሑፍ ብቻ ይላኩልኝ፤ ከዚያ የሚፈልጉትን ቋንቋ ይምረጡ።\n\n"
        "በጉጉት እየጠበቅኩዎት ነው! 👇"
    )
    bot.reply_to(message, welcome_text, parse_mode='Markdown')

@bot.message_handler(func=lambda message: True)
def handle_text(message):
    if message.text.startswith('/'): return
    user_data[message.chat.id] = message.text
    
    markup = types.InlineKeyboardMarkup(row_width=2)
    buttons = [types.InlineKeyboardButton(text, callback_data=code) 
               for code, text in lang_info.items()]
    markup.add(*buttons)
    
    bot.reply_to(message, "✅ ጽሁፉን ተቀብያለሁ!\nወደ የትኛው ቋንቋ ልተርጉምልዎ?", reply_markup=markup)

@bot.callback_query_handler(func=lambda call: True)
def callback_query(call):
    chat_id = call.message.chat.id
    target_lang = call.data
    original_text = user_data.get(chat_id)
    
    if not original_text:
        bot.send_message(chat_id, "⚠️ እባክዎ መጀመሪያ መተርጎም የሚፈልጉትን ጽሑፍ ይላኩልኝ።")
        return

    try:
        translator = GoogleTranslator(source='auto', target=target_lang)
        # ጽሁፍ ረጅም ከሆነ መከፋፈል
        if len(original_text) > 2000:
            part1 = original_text[:2000]
            part2 = original_text[2000:]
            translated = translator.translate(part1) + "\n\n" + translator.translate(part2)
        else:
            translated = translator.translate(original_text)
            
        result_text = f"🌍 **ትርጉም:**\n\n{translated}\n\n━━━━━━━━━━━━━━━━━━\n🤖 @vision_translator_bot"
        bot.send_message(chat_id, result_text, parse_mode='Markdown')
        
    except Exception:
        bot.send_message(chat_id, "⚠️ ይቅርታ፣ መተርጎም አልቻልኩም። እባክዎ ጽሁፉን በትንሹ ቀነስ አድርገው ይላኩት።")

bot.infinity_polling()

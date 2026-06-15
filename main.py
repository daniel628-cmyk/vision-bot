import telebot
from deep_translator import GoogleTranslator
from telebot import types

TOKEN = "8665976705:AAEkSumfgoiDkI01utc1QGEkrS2S50y59QQ"
bot = telebot.TeleBot(TOKEN)

# ለተጠቃሚዎች እና ለስታቲስቲክስ
user_data = {}
all_users = set() # ልዩ ተጠቃሚዎችን ለመቁጠር

lang_info = {
    "am": "🇪🇹", "en": "🇺🇸", 
    "om": "🇪🇹", "es": "🇪🇸", "fr": "🇫🇷"
}

@bot.message_handler(commands=['start'])
def send_welcome(message):
    user_name = message.from_user.first_name # የተጠቃሚው ስም
    all_users.add(message.chat.id) # ተጠቃሚውን መዝግብ
    
    welcome_text = (
        f"👋 **ሰላም፣ {user_name}!** ወደ **Vision ትርጉም ቦት** እንኳን በደህና መጡ!\n\n"
        f"👥 አሁን ቦቱን እየተጠቀሙ ያሉ ጠቅላላ ተጠቃሚዎች: {len(all_users)}\n\n"
        "ጽሑፎችን ወደ ፈለጉት ቋንቋ 🌍 በቀላሉ ለመተርጎም እረዳዎታለሁ።\n\n"
        "ለመጀመር፣ እባክዎ መተርጎም የሚፈልጉትን **ጽሑፍ ይላኩልኝ።**"
    )
    bot.reply_to(message, welcome_text, parse_mode='Markdown')

@bot.message_handler(func=lambda message: True)
def handle_text(message):
    if message.text.startswith('/'): return
    
    user_data[message.chat.id] = message.text
    
    markup = types.InlineKeyboardMarkup(row_width=2)
    buttons = [types.InlineKeyboardButton(f"{code.upper()} {flag}", callback_data=code) 
               for code, flag in lang_info.items()]
    markup.add(*buttons)
    
    bot.reply_to(message, "✅ ጽሁፉን ተቀብያለሁ! \nወደየትኛው ቋንቋ ልተርጉምልዎ?", reply_markup=markup)

@bot.callback_query_handler(func=lambda call: True)
def callback_query(call):
    chat_id = call.message.chat.id
    target_lang = call.data
    original_text = user_data.get(chat_id)
    
    try:
        translated = GoogleTranslator(source='auto', target=target_lang).translate(original_text)
        
        result_text = (
            f"{lang_info[target_lang]} {translated}\n\n"
            f"━━━━━━━━━━━━━━━━━━\n"
            f"🤖 @vision_translator_bot"
        )
        
        bot.reply_to(call.message, result_text, parse_mode='Markdown')
        bot.delete_message(chat_id, call.message.message_id)
        
    except Exception:
        bot.send_message(chat_id, "⚠️ ይቅርታ፣ መተርጎም አልቻልኩም።")

print("ቦቱ እየሰራ ነው...")
bot.polling(none_stop=True)

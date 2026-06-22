# ይህንን ከላይ ከማንኛውም message handler በፊት አስገባው
IS_MAINTENANCE = True # ጥገና ላይ ሲሆኑ True፣ ካልሆነ False ይበሉት

@bot.message_handler(func=lambda message: True)
def check_maintenance(message):
    if IS_MAINTENANCE:
        bot.reply_to(message, "🛠 **ቦቱ በአሁኑ ሰዓት ጥገና ላይ ነው!** 🚧\n\nበቅርቡ ተመልሰን እንመጣለን። አመሰግናለሁ! 🙏")
        return # ሌላ ምንም ነገር እንዳይሰራ ይከለክላል
    
    # ሌላው ኮድዎ ከዚህ በታች ይቀጥላል...

import os
import pytz
from datetime import time
from dotenv import load_dotenv
from telegram import Update
from telegram.ext import ApplicationBuilder, ContextTypes, MessageHandler, CommandHandler, filters
from agent import get_ai_response


#  Environment variables load karein
load_dotenv()

#  Telegram Bot Token environment variable se lein
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")

# --- 1.  MESSAGE HANDLER (Text, Photo, PDF) ---
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.effective_chat.id)
    user_text = update.message.text or ""
    image_url = None
    pdf_path = None

    # waiting message 
    waiting_msg = await update.message.reply_text("⏳ Dr. Sahayak आपकी फाइल चेक कर रहे हैं, कृपया इंतज़ार करें...")

    try:
        # image handle karna
        if update.message.photo:
            file = await context.bot.get_file(update.message.photo[-1].file_id)
            image_url = file.file_path
            user_text = update.message.caption or "Analyzing this image..."
            print(f"📸 Image received from {user_id}")

        # PDF handle karna
        elif update.message.document and update.message.document.mime_type == "application/pdf":
            pdf_file = await context.bot.get_file(update.message.document.file_id)
            pdf_path = f"report_{user_id}.pdf"
            
            # pdf file ko local drive par download karna
            
            await pdf_file.download_to_drive(pdf_path)
            user_text = update.message.caption or "Analyzing this PDF report..."
            print(f"📄 PDF received from {user_id}")

        print(f"📩 Message from {user_id}: {user_text}")

        # AI response generate karna (image_url aur pdf_path ke sath)
        
        response_text = get_ai_response(user_text, user_id=user_id, image_url=image_url, pdf_path=pdf_path)

        # waiting message delete karna aur AI response bhejna
        await context.bot.delete_message(chat_id=user_id, message_id=waiting_msg.message_id)
        await update.message.reply_text(response_text)

        # temporary files cleanup karna
        if pdf_path and os.path.exists(pdf_path):
            os.remove(pdf_path)

    except Exception as e:
        print(f"❌ Error in handle_message: {e}")
        if 'waiting_msg' in locals():
            await context.bot.delete_message(chat_id=user_id, message_id=waiting_msg.message_id)
        await update.message.reply_text("⚠️ माफ़ी चाहती हूँ, फाइल प्रोसेस करने में दिक्कत हुई।")


# --- 3. MAIN RUNNER ---
if __name__ == '__main__':
    print("🚀 Dr. Sahayak Bot is starting (Text + Photo + PDF + Reminders)...")
    
    # Telegram application setup karna
    application = ApplicationBuilder().token(TELEGRAM_TOKEN).read_timeout(60).connect_timeout(60).build()
    
    # Message handler add karna (text, photo, PDF)
    msg_handler = MessageHandler(filters.TEXT | filters.PHOTO | filters.Document.PDF, handle_message)
    application.add_handler(msg_handler)
    
    # Bot ko polling mode mein run karna
    application.run_polling()
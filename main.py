
# import os

# from dotenv import load_dotenv
# from datetime import time
# from telegram import Update
# from telegram.ext import ApplicationBuilder, ContextTypes, MessageHandler, CommandHandler, filters
# from agent import get_ai_response
# import pytz 

# load_dotenv()

# # ✅ अपना टेलीग्राम टोकन
# TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")

# async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
#     user_id = str(update.effective_chat.id)
#     user_text = update.message.text or ""
#     image_url = None
#     pdf_path = None

#     # यूजर को अपडेट देने के लिए एक छोटा सा मैसेज
#     waiting_msg = await update.message.reply_text("⏳ Dr. Sahayak आपकी फाइल चेक कर रहे हैं, कृपया इंतज़ार करें...")

#     try:
#         # 🖼️ 1. अगर यूजर ने फोटो भेजी है
#         if update.message.photo:
#             file = await context.bot.get_file(update.message.photo[-1].file_id)
#             image_url = file.file_path
#             user_text = update.message.caption or "Analyzing this image..."
#             print(f"📸 Image received from {user_id}")

#         # 📄 2. अगर यूजर ने PDF भेजी है
#         elif update.message.document and update.message.document.mime_type == "application/pdf":
#             pdf_file = await context.bot.get_file(update.message.document.file_id)
#             pdf_path = f"report_{user_id}.pdf"
#             # पीडीएफ को लोकली सेव करना
#             await pdf_file.download_to_drive(pdf_path)
#             user_text = update.message.caption or "Analyzing this PDF report..."
#             print(f"📄 PDF received from {user_id}")

#         print(f"📩 Message from {user_id}: {user_text}")

#         # एआई से रिस्पॉन्स लें (image_url और pdf_path दोनों पास कर रहे हैं)
#         response_text = get_ai_response(user_text, user_id=user_id, image_url=image_url, pdf_path=pdf_path)

#         # जवाब भेजने के बाद "Waiting" मैसेज डिलीट करें और असली जवाब भेजें
#         await context.bot.delete_message(chat_id=user_id, message_id=waiting_msg.message_id)
#         await update.message.reply_text(response_text)

#         # 🗑️ फाइल डिलीट करें ताकि कंप्यूटर भर न जाए
#         if pdf_path and os.path.exists(pdf_path):
#             os.remove(pdf_path)

#     except Exception as e:
#         print(f"❌ Error: {e}")
#         await update.message.reply_text("⚠️ माफ़ी चाहती हूँ, फाइल प्रोसेस करने में दिक्कत हुई। कृपया फिर से कोशिश करें।")
        
 

# # रिमाइंडर भेजने वाला फंक्शन
# async def send_reminder(context: ContextTypes.DEFAULT_TYPE):
#     job = context.job
#     await context.bot.send_message(job.chat_id, text=f"⏰ **Medicine Reminder:**\n\nAakash, aapki medicine **{job.data}** ka samay ho gaya hai. Kripya ise le lein! 💊")

# # रिमाइंडर सेट करने का कमांड
# async def set_reminder(update: Update, context: ContextTypes.DEFAULT_TYPE):
#     try:
#         # Format: /remind 08:00 Paracetamol
#         t_str = context.args[0]
#         med_name = " ".join(context.args[1:])
        
#         h, m = map(int, t_str.split(':'))
#         target_time = time(h, m, tzinfo=pytz.timezone('Asia/Kolkata'))
        
#         context.job_queue.run_daily(send_reminder, target_time, chat_id=update.effective_chat.id, data=med_name)
        
#         await update.message.reply_text(f"✅ Theek hai! Main rozana {t_str} baje aapko **{med_name}** ke liye remind karungi.")
#     except:
#         await update.message.reply_text("❌ Galat format! Use: `/remind HH:MM MedicineName` (e.g., /remind 20:30 Vitamin-D)")

# if __name__ == '__main__':
#     print("🚀 Dr. Sahayak Telegram Bot is starting (Text + Photo + PDF)...")
    
#     # टाइमआउट लिमिट बढ़ा दी है ताकि बड़ी रिपोर्ट्स आराम से प्रोसेस हों
#     application = ApplicationBuilder().token(TELEGRAM_TOKEN).read_timeout(60).connect_timeout(60).build()
    
#     # यहाँ PDF फिल्टर भी जोड़ दिया गया है
#     msg_handler = MessageHandler(filters.TEXT | filters.PHOTO | filters.Document.PDF, handle_message)
#     application.add_handler(msg_handler)
    
#     application.run_polling()

import os
import pytz
from datetime import time
from dotenv import load_dotenv
from telegram import Update
from telegram.ext import ApplicationBuilder, ContextTypes, MessageHandler, CommandHandler, filters
from agent import get_ai_response

# ✅ Environment variables load karein
load_dotenv()

# ✅ अपना टेलीग्राम टोकन
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")

# --- 1. 📂 MESSAGE HANDLER (Text, Photo, PDF) ---
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.effective_chat.id)
    user_text = update.message.text or ""
    image_url = None
    pdf_path = None

    # यूजर को 'Processing' मैसेज दिखाना
    waiting_msg = await update.message.reply_text("⏳ Dr. Sahayak आपकी फाइल चेक कर रहे हैं, कृपया इंतज़ार करें...")

    try:
        # 🖼️ फोटो हैंडलर
        if update.message.photo:
            file = await context.bot.get_file(update.message.photo[-1].file_id)
            image_url = file.file_path
            user_text = update.message.caption or "Analyzing this image..."
            print(f"📸 Image received from {user_id}")

        # 📄 PDF हैंडलर
        elif update.message.document and update.message.document.mime_type == "application/pdf":
            pdf_file = await context.bot.get_file(update.message.document.file_id)
            pdf_path = f"report_{user_id}.pdf"
            # PDF को लोकली सेव करना
            await pdf_file.download_to_drive(pdf_path)
            user_text = update.message.caption or "Analyzing this PDF report..."
            print(f"📄 PDF received from {user_id}")

        print(f"📩 Message from {user_id}: {user_text}")

        # AI (agent.py) से रिस्पॉन्स लेना
        response_text = get_ai_response(user_text, user_id=user_id, image_url=image_url, pdf_path=pdf_path)

        # पुराना मैसेज हटाकर AI का जवाब भेजना
        await context.bot.delete_message(chat_id=user_id, message_id=waiting_msg.message_id)
        await update.message.reply_text(response_text)

        # 🗑️ PDF फाइल डिलीट करना
        if pdf_path and os.path.exists(pdf_path):
            os.remove(pdf_path)

    except Exception as e:
        print(f"❌ Error in handle_message: {e}")
        if 'waiting_msg' in locals():
            await context.bot.delete_message(chat_id=user_id, message_id=waiting_msg.message_id)
        await update.message.reply_text("⚠️ माफ़ी चाहती हूँ, फाइल प्रोसेस करने में दिक्कत हुई।")

# --- 2. ⏰ MEDICINE REMINDER LOGIC ---
async def send_medicine_reminder(context: ContextTypes.DEFAULT_TYPE):
    job = context.job
    # 'Aakash' की जगह आप 'Dost' या generic नाम भी रख सकते हैं
    reminder_text = f"💊 **Medicine Reminder!**\n\nAakash, aapki medicine **{job.data}** ka samay ho gaya hai. Kripya ise turant le lein. Swasth rahein! 🙏"
    await context.bot.send_message(chat_id=job.chat_id, text=reminder_text)

async def set_reminder(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        # Format: /remind 20:30 Paracetamol
        time_str = context.args[0]
        medicine = " ".join(context.args[1:])
        
        # Time parse (HH:MM)
        hour, minute = map(int, time_str.split(':'))
        
        # Indian Timezone set करना
        ist = pytz.timezone('Asia/Kolkata')
        reminder_time = time(hour, minute, tzinfo=ist)
        
        # Job queue में डेली टास्क जोड़ना
        context.job_queue.run_daily(
            send_medicine_reminder, 
            time=reminder_time, 
            chat_id=update.effective_chat.id, 
            data=medicine,
            name=f"{update.effective_chat.id}_{medicine}" # Unique job name
        )
        
        await update.message.reply_text(f"✅ Done! Main rozana {time_str} baje aapko **{medicine}** ke liye remind karungi.")
    except Exception as e:
        print(f"❌ Reminder Error: {e}")
        await update.message.reply_text("❌ Galat format! Aise likhein: `/remind 08:30 Insulin`\n(24-hour format use karein)")
# रिमाइंडर हटाने वाला कमांड
async def remove_reminder(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # 'update.message' के बजाय 'update.effective_chat' इस्तेमाल करना बेहतर है
    chat_id = update.effective_chat.id
    
    try:
        medicine_to_remove = " ".join(context.args).strip()
        
        # अगर सिर्फ /stop लिखा है
        if not medicine_to_remove:
            all_jobs = context.job_queue.jobs()
            count = 0
            for job in all_jobs:
                if str(chat_id) in job.name:
                    job.schedule_removal()
                    count += 1
            
            msg = f"🗑️ Main ne aapke saare ({count}) active reminders hata diye hain." if count > 0 else "📭 Aapka koi active reminder nahi mila."
            await context.bot.send_message(chat_id=chat_id, text=msg)
            return

        # अगर नाम के साथ लिखा है (e.g., /stop Paracetamol)
        job_name = f"{chat_id}_{medicine_to_remove}"
        current_jobs = context.job_queue.get_jobs_by_name(job_name)
        
        if not current_jobs:
            await context.bot.send_message(chat_id=chat_id, text=f"❌ '{medicine_to_remove}' naam ka koi reminder nahi mila.")
            return

        for job in current_jobs:
            job.schedule_removal()
        
        await context.bot.send_message(chat_id=chat_id, text=f"✅ '{medicine_to_remove}' ka reminder band kar diya gaya hai.")
        
    except Exception as e:
        print(f"❌ Error in remove_reminder: {e}")
        # यहाँ भी context.bot.send_message इस्तेमाल करें
        await context.bot.send_message(chat_id=chat_id, text="⚠️ Reminder hatane mein thodi dikkat hui, please check karein.")
# --- 🚀 3. MAIN RUNNER ---
if __name__ == '__main__':
    print("🚀 Dr. Sahayak Bot is starting (Text + Photo + PDF + Reminders)...")
    
    # Application Build करना (JobQueue ऑटो-इनेबल हो जाती है अगर apscheduler इंस्टॉल है)
    application = ApplicationBuilder().token(TELEGRAM_TOKEN).read_timeout(60).connect_timeout(60).build()
    
    # कमांड हैंडलर (/remind)
    application.add_handler(CommandHandler("remind", set_reminder))
    
    # नया कमांड हैंडलर (रिमाइंडर हटाने के लिए)
    application.add_handler(CommandHandler("stop", remove_reminder))
    
    # मैसेज हैंडलर (Text, Photo, PDF)
    msg_handler = MessageHandler(filters.TEXT | filters.PHOTO | filters.Document.PDF, handle_message)
    application.add_handler(msg_handler)
    
    # बॉट शुरू करें
    application.run_polling()
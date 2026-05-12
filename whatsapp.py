import os
import requests
from fastapi import FastAPI, Request, Response, Form
from twilio.twiml.messaging_response import MessagingResponse
from twilio.rest import Client
from dotenv import load_dotenv
from agent import get_ai_response
from typing import Optional
from apscheduler.schedulers.background import BackgroundScheduler
import pytz

# ✅ Load env
load_dotenv()

app = FastAPI()

# ✅ Twilio Credentials
ACCOUNT_SID = os.getenv("TWILIO_ACCOUNT_SID")
AUTH_TOKEN = os.getenv("TWILIO_AUTH_TOKEN")
TWILIO_NUMBER = os.getenv("TWILIO_PHONE_NUMBER")

twilio_client = Client(ACCOUNT_SID, AUTH_TOKEN)

# ✅ Scheduler for Medicine Reminders
scheduler = BackgroundScheduler(timezone="Asia/Kolkata")
scheduler.start()

# 🧠 Temporary states for emergency
user_states = {}


# --- ⏰ REMINDER SENDING FUNCTION ---
def send_wa_reminder(chat_id, medicine):
    try:
        twilio_client.messages.create(
            from_=TWILIO_NUMBER,
            body=f"💊 **Ai_MedMitra Reminder!**\n\nAakash, aapki medicine **{medicine}** ka samay ho gaya hai. Kripya ise turant le lein. Swasth rahein! 🙏",
            to=chat_id,
        )
        print(f"✅ Reminder sent to {chat_id} for {medicine}")
    except Exception as e:
        print(f"❌ Reminder failed: {e}")


# --- 📞 EMERGENCY CALL FUNCTION ---
def emergency_call(phone_number):
    if not phone_number.startswith("+91"):
        phone_number = "+91" + phone_number[-10:]

    print("📞 Calling:", phone_number)
    try:
        call = twilio_client.calls.create(
            url="http://demo.twilio.com/docs/voice.xml",
            to=phone_number,
            from_=TWILIO_NUMBER,
        )
        return "📞 Emergency call initiated successfully. Stay on the line."
    except Exception as e:
        return f"❌ Call failed: {str(e)}"


# --- 🚀 MAIN WHATSAPP WEBHOOK ---
@app.post("/whatsapp")
async def whatsapp_bot(
    Body: str = Form(""),
    From: str = Form(""),
    MediaUrl0: Optional[str] = Form(None),
    MediaContentType0: Optional[str] = Form(None),
):
    user_id = From
    incoming_msg = Body.strip()
    text = incoming_msg.lower()

    image_path = None
    pdf_path = None

    # 1️⃣ 📂 FILE HANDLING (Authenticated Download Fix)
    if MediaUrl0:
        auth = (ACCOUNT_SID, AUTH_TOKEN)  # Twilio security key

        if "image" in MediaContentType0:
            ext = MediaContentType0.split("/")[-1]
            image_path = f"temp_img_{user_id[-4:]}.{ext}"
            resp = requests.get(MediaUrl0, auth=auth)
            if resp.status_code == 200:
                with open(image_path, "wb") as f:
                    f.write(resp.content)
                print(f"📸 Image saved locally: {image_path}")
            else:
                image_path = None

        elif "pdf" in MediaContentType0:
            pdf_path = f"report_wa_{user_id[-4:]}.pdf"
            resp = requests.get(MediaUrl0, auth=auth)
            if resp.status_code == 200:
                with open(pdf_path, "wb") as f:
                    f.write(resp.content)
                print(f"📄 PDF saved locally: {pdf_path}")
            else:
                pdf_path = None

    # 2️⃣ 🚨 EMERGENCY FLOW
    emergency_keywords = ["kill myself", "suicide", "want to die", "end my life"]

    if any(word in text for word in emergency_keywords):
        user_states[user_id] = "waiting_call_confirm"
        response_text = (
            "🚨 I'm here for you. Please don't lose hope.\n"
            "📞 AASRA: 9820466726\n"
            "If you want me to call you immediately, reply with YES."
        )

    elif user_states.get(user_id) == "waiting_call_confirm":
        if text == "yes":
            phone_number = user_id.replace("whatsapp:", "")
            user_states[user_id] = None
            response_text = emergency_call(phone_number)
        else:
            user_states[user_id] = None
            response_text = "Okay. I'm still here if you need to talk."

    # 3️⃣ ⏰ REMINDER COMMANDS
    elif text.startswith("/remind"):
        try:
            parts = incoming_msg.split(" ", 2)
            time_str = parts[1]
            med_name = parts[2]
            h, m = map(int, time_str.split(":"))

            job_id = f"{user_id}_{med_name}"
            scheduler.add_job(
                send_wa_reminder,
                "cron",
                hour=h,
                minute=m,
                args=[user_id, med_name],
                id=job_id,
                replace_existing=True,
            )
            response_text = f"✅ Done! Rozana {time_str} baje main aapko **{med_name}** ke liye remind karungi."
        except:
            response_text = (
                "❌ Galat format! Aise likhein: `/remind 08:30 MedicineName`"
            )

    elif text.startswith("/stop"):
        med_name = incoming_msg.replace("/stop", "").strip()
        job_id = f"{user_id}_{med_name}"
        try:
            scheduler.remove_job(job_id)
            response_text = f"🗑️ '{med_name}' ka reminder hata diya gaya hai."
        except:
            response_text = f"❓ '{med_name}' naam ka कोई reminder nahi mila."

    # 4️⃣ 🤖 NORMAL AI FLOW
    else:
        # AI (agent.py) se response lena
        # Note: image_url me hum local path bhej rahe hain
        response_text = get_ai_response(
            incoming_msg, user_id=user_id, image_url=image_path, pdf_path=pdf_path
        )

    # 5️⃣ 🗑️ CLEANUP (Delete temp files)
    if pdf_path and os.path.exists(pdf_path):
        os.remove(pdf_path)
    if image_path and os.path.exists(image_path):
        os.remove(image_path)

    # 📤 SEND RESPONSE
    tw_resp = MessagingResponse()
    tw_resp.message(response_text)
    return Response(content=str(tw_resp), media_type="application/xml")


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=5000)

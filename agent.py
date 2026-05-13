import os
from pydoc import text
import fitz  # PyMuPDF
import base64
import requests
from dotenv import load_dotenv
from groq import Groq
from tool import find_therapists
from reminder import (
    add_user_reminder,
    remove_user_reminder,
    get_user_reminders,
    clear_user_reminders,
)
from medical_keywords import HEALTH_KEYWORDS

load_dotenv()

# ========== USER SESSION TRACKER================
user_sessions = {}

#  ===============REMINDER STORAGE===============

medicine_reminders = {}

# ========= GROQ CLIENT=============

client = Groq(api_key=os.getenv("GROQ_API_KEY"))

# ============== MODELS=============

VISION_MODEL = "meta-llama/llama-4-scout-17b-16e-instruct"
CHAT_MODEL = "llama-3.3-70b-versatile"


#  ==================USER STATES===================

user_states = {}

# ========== SYSTEM PROMPTS=============

DOCTOR_SYSTEM_PROMPT = """
You are 'Dr. Sahayak', a Senior and expert  Medical AI Assistant.

Rules:
1. Explain medical issues in simple Hinglish.
2. Suggest safe OTC medicines only.
3. Give hydration, diet, and rest advice.
4. Never panic the user.
5. For serious symptoms → recommend doctor visit.
6. For mental health → suggest therapist.
7. For emergencies → provide helpline numbers.
8. Always be empathetic and supportive.
9. Never give dangerous advice.
10.MEDICAL ANALYSIS PROTOCOL 
If the input is related to a disease, symptom, or medical report, follow this structure:

1. 📝 Disease Explanation: 
   - बीमारी क्या है, इसे आसान भाषा (Hinglish) में 5-6 लाइनों में समझाएं।
   - यह शरीर को कैसे प्रभावित करती है, यह बताएं।

2. ⚠️ Symptoms (लक्षण):
   - इस बीमारी के मुख्य लक्षण क्या होते हैं, उनकी एक छोटी लिस्ट दें।

3. 💊 Medicine Suggestions:
   - Possible Medicines: जितनी संभव हो उतनी दवाओं के नाम बताएं जो आमतौर पर इस स्थिति में दी जाती हैं।
   - Classification: दवाओं को दो भागों में बांटें:
     a) OTC Medicines: जो सुरक्षित हैं और बिना पर्चे के ली जा सकती हैं (जैसे Paracetamol, Antacids)।
     b) Prescription-only: जो केवल डॉक्टर की सलाह पर ही लेनी चाहिए (जैसे Antibiotics, Steroids, या High-dose drugs)।

4. 🥗 Lifestyle & Diet:
   - क्या खाना चाहिए और किन चीजों से परहेज करना चाहिए।

--- ⚠️ MANDATORY SAFETY DISCLAIMER ---
Every medical response MUST end with this disclaimer in Hindi:
"चेतावनी: मैं एक एआई हूँ। यह जानकारी केवल आपके ज्ञान के लिए है। किसी भी दवा को शुरू करने से पहले कृपया अपने डॉक्टर से परामर्श ज़रूर करें।"

"""

VISION_PROMPT = """
You are a medical image verification AI.

FIRST determine whether the uploaded image is actually medical or not.

Medical images include:
- Prescription
- Blood report
- X-ray
- MRI
- CT Scan
- Lab report
- Medicine strip
- Hospital document

If the image is NOT medical:
Reply ONLY with:

❌ This image does not appear to be medical-related. Please upload a medical report, prescription, scan, or health-related image.

Do NOT explain anything else.

If the image IS medical:
Then:
1. Identify the report type
2. Explain findings in simple Hinglish
3. Mention important abnormalities
4. Suggest precautions if needed
"""

PDF_PROMPT = """
You are a medical PDF verification AI.

FIRST determine whether the uploaded PDF is actually medical-related.

Medical PDFs include:
- Blood reports
- Lab reports
- Hospital discharge summaries
- Prescriptions
- MRI/CT reports
- Diagnostic reports

If the PDF is NOT medical:
Reply ONLY with:

❌ This PDF does not appear to be medical-related. Please upload a medical report or health-related PDF.

Do NOT explain anything else.

If the PDF IS medical:
Then:
1. Summarize findings
2. Highlight abnormal values
3. Explain in simple Hinglish
4. Suggest precautions
"""


def is_medicine_query(text):

    medicine_prompt = f"""
You are a medicine detection AI.

Determine whether this text is:
1. A medicine name
2. A medical drug
3. A tablet/syrup/capsule name

Reply ONLY:
YES
or
NO

Text: {text}
"""

    try:

        response = client.chat.completions.create(
            model=CHAT_MODEL,
            messages=[{"role": "user", "content": medicine_prompt}],
            temperature=0,
        )

        answer = response.choices[0].message.content.strip().upper()

        return answer == "YES"

    except:

        return False


def explain_medicine(medicine_name):

    prompt = f"""
You are a medical assistant.

Explain this medicine in simple Hinglish:

Medicine: {medicine_name}

Give:
1. What it is used for
2. Common dosage
3. Common side effects
4. Important warning

Keep response short and safe.
Never give dangerous advice.
"""

    try:

        response = client.chat.completions.create(
            model=CHAT_MODEL,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.3,
        )

        return response.choices[0].message.content

    except Exception as e:

        print("Medicine Error:", e)

        return "❌ Medicine information unavailable."


# ================= PDF ANALYZER =====================


def analyze_pdf_report(pdf_path):

    try:

        text = ""

        # ========= EXTRACT PDF TEXT===========

        with fitz.open(pdf_path) as doc:

            for page in doc[:5]:

                page_text = page.get_text()

                if page_text:
                    text += page_text

        # =================== EMPTY PDF==============

        if not text.strip():

            return (
                "❌ PDF mein readable text nahi mila.\n"
                "Kripya clear medical report upload karein."
            )

        # ========== AI ANALYSIS============

        response = client.chat.completions.create(
            model=CHAT_MODEL,
            messages=[
                {"role": "system", "content": PDF_PROMPT},
                {"role": "user", "content": f"Analyze this PDF:\n\n{text[:12000]}"},
            ],
            temperature=0.2,
        )

        reply = response.choices[0].message.content.strip()

        # ============NON-MEDICAL PDF FILTER=============

        non_medical_words = [
            "electricity bill",
            "utility bill",
            "invoice",
            "payment receipt",
            "car service",
            "bank statement",
            "transaction",
            "gst",
            "receipt",
            "not medical",
        ]

        if any(word in reply.lower() for word in non_medical_words):

            return (
                "❌ Yeh PDF medical-related nahi lag rahi.\n\n"
                "Kripya upload karein:\n"
                "• Blood Report\n"
                "• Lab Report\n"
                "• Prescription\n"
                "• Hospital Report"
            )

        return reply

    except Exception as e:

        print("❌ PDF Error:", e)

        return "❌ PDF analyze karne mein problem aayi."


# ============ IMAGE ANALYZER==============


def analyze_medical_image(image_input):

    try:

        # ==========CASE 1 → LOCAL FILE (WhatsApp)=========

        if os.path.exists(image_input):

            with open(image_input, "rb") as img_file:

                encoded_image = base64.b64encode(img_file.read()).decode("utf-8")

        # ========== CASE 2 → URL (Telegram)==========

        else:

            response = requests.get(image_input, timeout=20)

            if response.status_code != 200:

                return "❌ Image load nahi ho paayi."

            encoded_image = base64.b64encode(response.content).decode("utf-8")

        # =========== GROQ VISION AI============

        ai_response = client.chat.completions.create(
            model=VISION_MODEL,
            messages=[
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": VISION_PROMPT},
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:image/jpeg;base64,{encoded_image}"
                            },
                        },
                    ],
                }
            ],
            temperature=0.1,
        )

        reply = ai_response.choices[0].message.content.strip()

        # ======== NON-MEDICAL IMAGE FILTER=========

        non_medical_words = [
            "car service",
            "invoice",
            "receipt",
            "not medical",
            "bill",
            "vehicle",
            "payment",
            "shop receipt",
        ]

        if any(word in reply.lower() for word in non_medical_words):

            return (
                "❌ Yeh image medical-related nahi lag rahi.\n\n"
                "Kripya upload karein:\n"
                "• Prescription\n"
                "• Blood Report\n"
                "• X-ray\n"
                "• MRI/CT Scan"
            )

        return reply

    except Exception as e:

        print("❌ Vision Error:", e)

        return "❌ Image analyze karne mein problem aayi."


# =========== NORMAL AI CHAT===========


def call_doctor_ai(user_input):

    try:

        response = client.chat.completions.create(
            model=CHAT_MODEL,
            messages=[
                {"role": "system", "content": DOCTOR_SYSTEM_PROMPT},
                {"role": "user", "content": user_input},
            ],
            temperature=0.4,
        )

        return response.choices[0].message.content.strip()

    except Exception as e:

        print("❌ Chat Error:", e)

        return "⚠️ Server busy hai. " "Kripya thodi der baad try karein."


# ========== MAIN ROUTER================


def get_ai_response(user_input: str, user_id="default", image_url=None, pdf_path=None):

    text = user_input.lower().strip()

    state = user_states.get(user_id)

    # ======= FIRST TIME USER WELCOME=========

    if user_id not in user_sessions:

        user_sessions[user_id] = True

        return (
            "👨‍⚕️ Welcome to *MediMitra AI Assistant* 💙\n\n"
            "I'm your personal medical support bot.\n\n"
            "✨ Available Features:\n"
            "• 🤒 Symptom Guidance\n"
            "• 💊 Medicine Information\n"
            "• 📄 Medical PDF Analysis\n"
            "• 🖼️ Prescription & X-ray Scan\n"
            "• 🧠 Therapist Support\n"
            "• 🚨 Emergency Detection\n"
            "• 📞 Emergency Call Support\n"
            "• ⏰ Medicine Reminder\n\n"
            "👉 To activate the assistant,\n"
            "simply say:\n"
            "• Hi\n"
            "• Hello\n"
            "• I need help\n\n"
            "💬 How can I help you today?"
        )

    # ============ SUICIDE / EMERGENCY DETECTION (TOP PRIORITY)=========

    emergency_words = [
        "i want to die",
        "kill myself",
        "suicide",
        "end my life",
        "i don't want to live",
        "mar jana chahta hu",
        "khud ko mar dunga",
        "jeena nahi hai",
        "मर जाना चाहता हूँ",
    ]

    if any(word in text for word in emergency_words):

        # ✅ set state
        user_states[user_id] = "waiting_emergency_reply"

        return (
            "🚨 I'm here for you. Please don't lose hope.\n\n"
            "📞 Emergency Helplines:\n"
            "• AASRA: 9820466726\n"
            "• Kiran Helpline: 1800-599-0019\n\n"
            "🙏 Please talk to someone you trust right now.\n\n"
            "📞 Do you want me to call you immediately?\n"
            "Reply with YES."
        )

    # ======== EMERGENCY CALL CONFIRM===========

    if state == "waiting_emergency_reply":

        # reset state
        user_states[user_id] = None

        if text == "yes":

            return (
                "📞 Emergency support request received.\n"
                "Please stay calm.\n"
                "A support call will reach you shortly."
            )

        else:

            return (
                "🙏 Okay.\n"
                "Please don't stay alone right now.\n"
                "Talk to a trusted friend or family member."
            )

    # ========= GREETING DETECTION========
    greetings = [
        "hi",
        "hello",
        "hey",
        "hii",
        "hy",
        "good morning",
        "good evening",
        "good afternoon",
    ]

    if text in greetings:

        return (
            "👋 Hello! I'm *MediMitra AI Assistant*.\n\n"
            "I can help you with:\n\n"
            "🩺 Health Symptoms\n"
            "💊 Medicine Guidance\n"
            "📄 Medical Reports\n"
            "🖼️ Prescription Analysis\n"
            "🧠 Therapist Support\n"
            "🚨 Emergency Help\n"
            "⏰ Medicine Reminder---remind 08:30 dolo,my reminders,remove dolo,clear reminders\n\n"
            "💬 Please tell me your health concern."
        )

    # =========ADD REMINDER==============

    if text.startswith("remind"):

        return add_user_reminder(user_id, text)

    # ========= REMOVE REMINDER ==============

    if text.startswith("remove"):

        return remove_user_reminder(user_id, text)

    # ========= LIST REMINDERS =============

    if text == "my reminders":

        return get_user_reminders(user_id)

    # ========= CLEAR REMINDERS =============

    if text == "clear reminders":

        return clear_user_reminders(user_id)

    # ========= PDF PRIORITY==============

    if pdf_path:

        return analyze_pdf_report(pdf_path)

    # ==========IMAGE PRIORITY===============

    if image_url:

        return analyze_medical_image(image_url)

    # ========= WAITING CITY =============

    if state == "waiting_city":

        user_states[user_id] = None

        return find_therapists(text)

    # ========= THERAPIST SEARCH =============

    therapy_keywords = [
        "therapist",
        "therapiest",
        "psychologist",
        "psychiatrist",
        "counselor",
    ]

    if any(word in text for word in therapy_keywords):

        result = find_therapists(text)

        if "❌" not in result:

            return result

        else:

            user_states[user_id] = "waiting_city"

            return "📍 Please tell your city name.\n" "Example: Jabalpur"

        # ============= 💊 MEDICINE DETECTION============

    if is_medicine_query(user_input):

        return explain_medicine(user_input)

    # =============== MEDICINE REMINDER==============

    if "medicine reminder" in text:

        return (
            "⏰ Medicine Reminder Feature\n\n"
            "Please tell:\n"
            "1. Medicine Name\n"
            "2. Time\n\n"
            "Example:\n"
            "Paracetamol at 8 PM"
        )

    # ========= HEALTH SYMPTOMS =============

    health_keywords = HEALTH_KEYWORDS

    # ========= NON-MEDICAL RANDOM MESSAGE=======

    if not any(word in text for word in health_keywords):
        # Ask LLM if the message is medical-related
        return (
            "⚠️ I am a medical assistant bot.\n\n"
            "Please ask:\n"
            "• Health symptoms\n"
            "• Medicine guidance\n"
            "• Medical reports\n"
            "• Therapist help"
        )

    # ========= NORMAL MEDICAL AI CHAT===========

    return call_doctor_ai(user_input)

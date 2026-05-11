

import os
import fitz  # PyMuPDF
import base64
import requests
from dotenv import load_dotenv
from groq import Groq
from tool import find_therapists

load_dotenv()

# ✅ Groq Client Setup
client = Groq(api_key=os.getenv("GROQ_API_KEY"))

# ✅ Stable 2026 Models
VISION_MODEL = "meta-llama/llama-4-scout-17b-16e-instruct" 
CHAT_MODEL = "llama-3.3-70b-versatile"

user_states = {}  # यूजर स्टेट ट्रैकिंग के लिए

# --- 🧠 SYSTEM PROMPTS ---

DOCTOR_SYSTEM_PROMPT = """
You are 'Dr. Sahayak', a Senior Medical AI & Nutritionist. 
1. If a user asks about a disease (Diabetes, BP, Thyroid), provide a structured 'Diet Chart' (Kya khayein/Kya na khayein).
2. Give clear breakfast, lunch, and dinner suggestions in Hinglish.
3. Suggest common OTC medicines with safety warnings.
4. Keep the tone empathetic and professional.
"""


VISION_PROMPT = """
You are an Expert Medical Radiologist. Analyze this image (X-ray, Prescription, or Report):
1. Identify what this is. 
2. Explain findings in simple Hinglish.
3. Highlight critical issues if any.
"""

PDF_PROMPT = """
You are a Medical Specialist. Analyze the following text extracted from a medical report PDF:
1. Summarize the findings.
2. Identify abnormal values (High/Low) and explain them in Hinglish.
3. Suggest next steps or lifestyle advice.
"""

# --- 📄 PDF EXTRACTION FUNCTION ---
def analyze_pdf_report(pdf_path):
    try:
        text = ""
        with fitz.open(pdf_path) as doc:
            # पहले 5 पेज स्कैन करें
            for page in doc[:5]:
                text += page.get_text()
        
        if not text.strip():
            return "❌ PDF में कोई टेक्स्ट नहीं मिला (शायद यह इमेज-बेस्ड PDF है)। कृपया इसकी फोटो खींचकर भेजें।"

        response = client.chat.completions.create(
            model=CHAT_MODEL,
            messages=[
                {"role": "system", "content": PDF_PROMPT},
                {"role": "user", "content": f"Analyze this report text:\n\n{text}"}
            ],
            temperature=0.3
        )
        return response.choices[0].message.content
    except Exception as e:
        print(f"❌ PDF Error: {e}")
        return "❌ PDF फाइल पढ़ने में समस्या आई है।"

# --- 🖼️ ENHANCED VISION ANALYSIS (Variable Fix Done) ---
def analyze_medical_image(image_url):
    try:
        response = requests.get(image_url, timeout=15)
        if response.status_code != 200:
            return "❌ रिपोर्ट लोड नहीं हो पाई। कृपया फिर से फोटो भेजें।"

        # Variable naming fix: Using 'encoded_image' consistently
        encoded_image = base64.b64encode(response.content).decode('utf-8')

        ai_response = client.chat.completions.create(
            model=VISION_MODEL,
            messages=[
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": VISION_PROMPT},
                        {
                            "type": "image_url",
                            "image_url": {"url": f"data:image/jpeg;base64,{encoded_image}"}
                        }
                    ]
                }
            ],
            temperature=0.1
        )
        return ai_response.choices[0].message.content

    except Exception as e:
        print(f"❌ Specialist Vision Error: {e}")
        return "❌ माफ़ी चाहती हूँ, इस रिपोर्ट को पढ़ने में कुछ दिक्कत आ रही है।"

# --- 💬 ADVANCED DOCTOR CHAT ---
def call_doctor_ai(user_input):
    try:
        response = client.chat.completions.create(
            model=CHAT_MODEL,
            messages=[
                {"role": "system", "content": DOCTOR_SYSTEM_PROMPT},
                {"role": "user", "content": user_input}
            ],
            temperature=0.4
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        return "⚠️ सर्वर अभी थोड़ा बिजी है। इमरजेंसी में पास के अस्पताल जाएँ।"

# --- 🚀 MAIN ROUTER (Fully Functional) ---
def get_ai_response(user_input: str, user_id="default", image_url=None, pdf_path=None):
    text = user_input.lower().strip()
    state = user_states.get(user_id)

    # 1. प्राथमिकता: PDF या Photo
    if pdf_path: return analyze_pdf_report(pdf_path)
    if image_url: return analyze_medical_image(image_url)

    # 2. स्टेट हैंडलिंग (अगर बॉट शहर का इंतज़ार कर रहा है)
    if state == "waiting_city":
        user_states[user_id] = None # स्टेट क्लियर करें
        return find_therapists(text)

    # 3. थेरेपिस्ट/डॉक्टर सर्च लॉजिक (यहीं गड़बड़ हो रही थी)
    therapy_keywords = ["therapist", "psychologist", "psychiatrist", "doctor search", "counselor"]
    if any(word in text for word in therapy_keywords):
        # अगर यूजर ने शहर का नाम मैसेज में ही लिख दिया है (e.g. "Therapist in Jabalpur")
        result = find_therapists(text)
        if "❌" not in result: # अगर शहर मिल गया
            return result
        else:
            # अगर शहर नहीं मिला, तो स्टेट बदलें और शहर पूछें
            user_states[user_id] = "waiting_city"
            return "📍 मैं आपकी मदद कर सकता हूँ। कृपया अपने शहर का नाम बताएं? (जैसे: Jabalpur)"

    # 4. इमरजेंसी चेक
    if any(word in text for word in ["emergency", "suicide", "bleeding"]):
        return "🚨 **इमरजेंसी!** कृपया तुरंत 108 पर कॉल करें।"
    
    if "sos" in text or "help me" in text:
       return "🚨 **EMERGENCY DETECTED!** 🚨\n\nMain help mang rahi hoon. Kripya apna **Live Location** niche diye gaye 'Attachment' icon se share karein taaki main use save kar sakoon!"

    # 5. नॉर्मल डॉक्टर चैट (Groq AI)
    return call_doctor_ai(user_input)
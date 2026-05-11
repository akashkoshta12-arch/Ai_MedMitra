

import os
from twilio.rest import Client
from dotenv import load_dotenv

load_dotenv()

# Twilio Setup
account_sid = os.getenv("TWILIO_ACCOUNT_SID")
auth_token = os.getenv("TWILIO_AUTH_TOKEN")
client = Client(account_sid, auth_token) if account_sid and auth_token else None

# 🏥 Expandable Therapist Database
THERAPISTS_DB = {
    "jabalpur": [
        {"name": "Dr. Sarang Pandit", "loc": "Napier Town", "phone": "+917067671223"},
        {"name": "Abhilakshya Mind Clinic", "loc": "Wright Town", "phone": "+917303183233"}
    ],
    "gwalior": [
        {"name": "Dr. Rahul Gupta", "loc": "City Center", "phone": "+919826200000"}
    ],
    "bhopal": [
        {"name": "Dr. Alok Agrawal", "loc": "Arera Colony", "phone": "+917550000000"}
    ],
    "indore": [
        {"name": "Dr. Swati Sharma", "loc": "Vijay Nagar", "phone": "+917310000000"}
    ],
    "delhi": [
        {"name": "Vimhans Niyati", "loc": "Nehru Nagar", "phone": "+911100000000"}
    ]
}

def emergency_call(phone_number: str):
    if not client:
        return "❌ Twilio API key missing or balance exhausted."
    
    phone_number = phone_number.strip()
    if not phone_number.startswith("+91") and len(phone_number) == 10:
        phone_number = "+91" + phone_number

    try:
        call = client.calls.create(
            url='http://demo.twilio.com/docs/voice.xml',
            to=phone_number,
            from_=os.getenv("TWILIO_PHONE_NUMBER")
        )
        return "📞 Emergency call initiated. Help is on the way."
    except Exception as e:
        return f"❌ Call failed: {str(e)}"

def find_therapists(user_input: str):
    """
    यह फंक्शन अब यूजर के पूरे मैसेज में से शहर का नाम ढूंढ लेगा।
    उदाहरण: 'I am in Jabalpur' में से यह 'Jabalpur' पहचान लेगा।
    """
    text = user_input.lower().strip()
    
    found_city = None
    for city in THERAPISTS_DB.keys():
        if city in text: # अगर मैसेज में शहर का नाम कहीं भी है
            found_city = city
            break
            
    if found_city:
        res = f"🔍 Nearby specialists in {found_city.title()}:\n\n"
        for t in THERAPISTS_DB[found_city]:
            res += f"🧑‍⚕️ **{t['name']}**\n📍 {t['loc']}\n📞 {t['phone']}\n\n"
        res += "👉 Aap in numbers par call karke appointment le sakte hain. Stay strong!"
        return res
    
    return (
        f"❌ Maafi chahti hoon, mere paas abhi sirf in cities ka data hai: \n"
        f"📍 {', '.join(THERAPISTS_DB.keys()).title()}\n\n"
        "Kya aap inmein se kisi city ke bare mein jaanna chahte hain?"
    )



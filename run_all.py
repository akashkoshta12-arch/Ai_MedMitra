import multiprocessing
import os
import uvicorn
from fastapi import FastAPI
from contextlib import asynccontextmanager

# ======BOT RUNNER FUNCTIONS ======

def run_telegram():
    """टेलीग्राम सर्विस शुरू करने के लिए"""
    print("🤖 [Telegram] सर्विस शुरू हो रही है...")
    try:
        # 'python' की जगह 'python.exe' भी लिख सकते हैं अगर विंडोज पर हैं
        os.system("python main.py")
    except Exception as e:
        print(f"❌ [Telegram] Error: {e}")

def run_whatsapp():
    """व्हाट्सएप सर्विस शुरू करने के लिए"""
    print("📲 [WhatsApp] सर्विस शुरू हो रही है...")
    try:
        os.system("python whatsapp.py")
    except Exception as e:
        print(f"❌ [WhatsApp] Error: {e}")

# --- 🚀 LIFESPAN MANAGER (Startup & Shutdown) ---

# ये ग्लोबल वेरिएबल्स हैं ताकि शटडाउन के समय इन्हें एक्सेस किया जा सके
processes = []

@asynccontextmanager
async def lifespan(app: FastAPI):
    # सर्वर शुरू होते समय का लॉजिक
    print("--- 🏥 Ai_MedMitra Unified Server Starting ---")
    
    p_tg = multiprocessing.Process(target=run_telegram, name="TG_Bot")
    p_wa = multiprocessing.Process(target=run_whatsapp, name="WA_Bot")
    
    processes.append(p_tg)
    processes.append(p_wa)
    
    for p in processes:
        p.start()
    
    yield  # server running...status
    
    # सर्वर बंद होते समय का लॉजिक (Ctrl+C दबाने पर)
    print("\n🛑 सर्वर बंद किया जा रहा है...")
    for p in processes:
        p.terminate()
        p.join()
    print("✅ Ai_MedMitra की दोनों सर्विस सुरक्षित रूप से बंद कर दी गई हैं।")

# ======== FASTAPI APP =========

app = FastAPI(lifespan=lifespan)

@app.get("/")
async def root():
    return {
        "project": "Ai_MedMitra",
        "status": "Running",
        "services": ["Telegram", "WhatsApp"],
        "message": "Unified medical bot server is active."
    }

@app.get("/health")
async def health_check():
    # checking if processes are alive
    status = {p.name: "Alive" if p.is_alive() else "Dead" for p in processes}
    return {"status": status}

# ======= RUN COMMAND =======
if __name__ == '__main__':
    #  'uvicorn run_all:app --reload' 
    uvicorn.run(app, host="0.0.0.0", port=8000)

import os
import time
import requests
import urllib3
import io
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from dotenv import load_dotenv
from fastapi.responses import StreamingResponse

# ביטול אזהרות נטפרי
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
load_dotenv()

app = FastAPI()

# הגדרת CORS - חשוב מאוד כדי שה-React יוכל לדבר עם השרת
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# שליפת מפתחות
API_KEY = os.getenv("GOOGLE_API_KEY")
ELEVENLABS_API_KEY = os.getenv("ELEVENLABS_API_KEY")
VOICE_ID = "pNInz6obpgDQGcFmaJgB" 

# כתובת תקינה כולל v1beta
GEMINI_URL = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent?key={API_KEY}"

class ChatRequest(BaseModel):
    messages: list
    is_finished: bool = False

def get_system_prompt():
    try:
        base_path = os.path.dirname(__file__)
        prompt_path = os.path.join(base_path, "prompts", "Car-insurance.txt")
        if os.path.exists(prompt_path):
            with open(prompt_path, "r", encoding="utf-8") as f:
                return f.read()
    except Exception as e:
        print(f"Error loading prompt: {e}")
    return "אתה נציג שירות לקוחות. ענה בעברית."

@app.post("/chat")
async def chat_with_ai(request: ChatRequest):
    try:
        system_prompt = get_system_prompt()
        formatted_contents = []
        
        # הוספת הפרומפט כהנחיה ראשונה
        formatted_contents.append({
            "role": "user",
            "parts": [{"text": f"Instruction: {system_prompt}"}]
        })
        
        # אישור של המודל
        formatted_contents.append({
            "role": "model", 
            "parts": [{"text": "אני מוכן לסימולציה. שלום, אני נציג שירות הלקוחות שלך."}]
        })

        # הוספת היסטוריית ההודעות
        for msg in request.messages:
            role = "user" if msg.get("role") == "user" else "model"
            content = msg.get("content", "")
            if content.strip(): 
                formatted_contents.append({
                    "role": role,
                    "parts": [{"text": content}]
                })

        # הוספת הטיפול בסיום השיחה - הוספת בקשת המשוב וה-JSON להודעה האחרונה של הלקוח
        if request.is_finished:
            text_to_add = """
\n\nהשיחה הסתיימה כעת. 
1. קודם כל, כתוב משוב מילולי מפורט בעברית. התייחס ספציפית לאמפתיה של הנציג, רמת ההקשבה, מקצועיות וסבלנות.
2. לאחר מכן, בסוף התגובה, צור בלוק JSON נקי ותקין (עטוף ב- ```json ו- ```). 
חשוב מאוד: מפתחות ה-JSON חייבים להיות באנגלית בלבד. אל תערבב טקסט חופשי בתוך ה-JSON!
"""
            if formatted_contents and formatted_contents[-1]["role"] == "user":
                formatted_contents[-1]["parts"][0]["text"] += text_to_add
            else:
                formatted_contents.append({"role": "user", "parts": [{"text": text_to_add}]})

        payload = {
            "contents": formatted_contents,
            "generationConfig": {
                "temperature": 0.7,
                "maxOutputTokens": 2000,
            },
            "safetySettings": [
                {"category": "HARM_CATEGORY_HARASSMENT", "threshold": "BLOCK_NONE"},
                {"category": "HARM_CATEGORY_HATE_SPEECH", "threshold": "BLOCK_NONE"},
                {"category": "HARM_CATEGORY_SEXUALLY_EXPLICIT", "threshold": "BLOCK_NONE"},
                {"category": "HARM_CATEGORY_DANGEROUS_CONTENT", "threshold": "BLOCK_NONE"},
            ]
        }
        
        # מנגנון Retry חזק (השהיה מתגברת לעומסי גוגל)
        max_retries = 4
        
        for attempt in range(max_retries):
            try:
                response = requests.post(GEMINI_URL, json=payload, verify=False, timeout=120)
                
                if not response.text:
                    raise Exception("Empty response from Gemini API")
                
                try:
                    data = response.json()
                except Exception:
                    raise Exception(f"The API returned a non-JSON response. Raw: {response.text}")
                
                if response.status_code == 200:
                    break
                
                error_msg = data.get("error", {}).get("message", "Unknown API Error")
                print(f"API Error Detected on attempt {attempt + 1}: {error_msg}")
                
                if response.status_code in [503, 429] and attempt < max_retries - 1:
                    retry_delay = (attempt + 1) * 3
                    print(f"Server busy. Retrying in {retry_delay} seconds...")
                    time.sleep(retry_delay)
                    continue
                else:
                    raise HTTPException(status_code=response.status_code, detail=error_msg)
                    
            except Exception as e:
                if attempt < max_retries - 1 and not isinstance(e, HTTPException):
                    retry_delay = (attempt + 1) * 3
                    print(f"Request failed (attempt {attempt + 1}): {str(e)}. Retrying in {retry_delay}s...")
                    time.sleep(retry_delay)
                else:
                    if isinstance(e, HTTPException):
                        raise e
                    raise HTTPException(status_code=500, detail=str(e))

        # שליפת הטקסט ומניעת קריסת ה-KeyError
        try:
            ai_text = data['candidates'][0]['content']['parts'][0]['text']
            return {"response": ai_text}
        except KeyError:
            print(f"Unexpected JSON structure (No parts found): {data}")
            return {"response": "שגיאה פנימית מהמודל - ייתכן שנחסם תוכן. נא לנסות לענות שוב."}

    except HTTPException as he:
        # כאן אנחנו זורקים את השגיאה (למשל 503) הלאה ל-React כדי שהוא יטפל בה באלגנטיות
        raise he
    except Exception as e:
        print(f"SERVER CRASH: {str(e)}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))

# --- נתיב ה-TTS ---
@app.post("/tts")
async def text_to_speech(request: dict):
    try:
        text = request.get("text")
        if not text:
            raise HTTPException(status_code=400, detail="No text")

        url = f"https://api.elevenlabs.io/v1/text-to-speech/{VOICE_ID}"
        headers = {
            "Accept": "audio/mpeg",
            "Content-Type": "application/json",
            "xi-api-key": ELEVENLABS_API_KEY.strip()
        }
        data = {
            "text": text,
            "model_id": "eleven_v3", # מודל יציב שתומך בעברית מצוין
            "voice_settings": {"stability": 0.5, "similarity_boost": 0.5}
        }

        response = requests.post(url, json=data, headers=headers, verify=False)
        
        if response.status_code == 200:
            return StreamingResponse(io.BytesIO(response.content), media_type="audio/mpeg")
        else:
            print(f"ElevenLabs Error: {response.status_code} - {response.text}")
            raise HTTPException(status_code=response.status_code, detail="TTS Failed")
            
    except Exception as e:
        print(f"TTS Route Error: {e}")
        raise HTTPException(status_code=500, detail=str(e))
    
# רשימות זמניות לשמירת נתונים
feedbacks_db = []
topics_db = []

class FeedbackRequest(BaseModel):
    agent_name: str
    simulation_topic: str
    score: int
    feedback_text: str
    ai_json_summary: dict = None

class TopicRequest(BaseModel):
    title: str
    prompt_instructions: str

@app.get("/api/feedbacks")
async def get_feedbacks():
    return {"feedbacks": feedbacks_db}

@app.post("/api/feedbacks")
async def save_feedback(feedback: FeedbackRequest):
    feedbacks_db.append(feedback.model_dump())
    return {"status": "success", "message": "Feedback saved"}

@app.get("/api/topics")
async def get_topics():
    return {"topics": topics_db}

@app.post("/api/topics")
async def add_topic(topic: TopicRequest):
    topics_db.append(topic.model_dump())
    return {"status": "success", "message": "Topic added"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
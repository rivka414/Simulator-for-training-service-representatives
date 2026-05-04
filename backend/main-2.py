import os
import time
import requests
import urllib3
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from dotenv import load_dotenv

# 1. הגדרות עבור נטפרי - ביטול אזהרות ואימות SSL
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
load_dotenv()

app = FastAPI()

# 2. הגדרת CORS - מאפשר ל-React לתקשר עם ה-Backend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# 3. הגדרות ה-API
API_KEY = os.getenv("GOOGLE_API_KEY")

# שימוש בכתובת התקינה למודל 2.5
GEMINI_URL = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent?key={API_KEY}"

# טעינת ה-System Prompt מקובץ חיצוני
try:
    prompt_path = os.path.join(os.path.dirname(__file__), "prompts", "Car-insurance.txt")
    with open(prompt_path, "r", encoding="utf-8") as f:
        SYSTEM_PROMPT = f.read()
except FileNotFoundError:
    SYSTEM_PROMPT = "You are a helpful customer service simulator."
    print("Warning: Car-insurance.txt not found. Using default prompt.")

class ChatRequest(BaseModel):
    messages: list
    is_finished: bool = False

@app.post("/chat")
async def chat_with_ai(request: ChatRequest):
    try:
        print(f"--- Processing request (Messages count: {len(request.messages)}) ---")
        
        # בניית מבנה ה-Contents עבור Gemini
        contents = []
        
        # הזרקת ההוראות והתחלת הסימולציה כהודעת מערכת/משתמש ראשונה
        contents.append({"role": "user", "parts": [{"text": f"Instruction: {SYSTEM_PROMPT}"}]})
        contents.append({"role": "model", "parts": [{"text": "הבנתי. אני מוכן להתחיל בתור ישראל הלקוח. שלום."}]})
        
        # הוספת היסטוריית השיחה מה-Frontend
        for msg in request.messages:
            role = "user" if msg["role"] == "user" else "model"
            contents.append({"role": role, "parts": [{"text": msg["content"]}]})
        
        # טיפול בסיום שיחה - בקשת משוב (מניעת כפילות של Role: user)
        if request.is_finished:
            text_to_add = "\n\nהשיחה הסתיימה כעת. ספק את המשוב המפורט ואת ה-JSON כפי שהתבקשת בהוראות המקוריות."
            
            # אם ההודעה האחרונה ברשימה היא של המשתמש (user), נוסיף לה את הטקסט כדי למנוע כפילות תפקידים
            if contents and contents[-1]["role"] == "user":
                contents[-1]["parts"][0]["text"] += text_to_add
            # אם לא, נוסיף כבלוק חדש
            else:
                contents.append({"role": "user", "parts": [{"text": text_to_add}]})

        payload = {
            "contents": contents,
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

        # --- הוספת מנגנון Retry עם השהיה מתגברת (Exponential Backoff) ---
        max_retries = 4
        
        for attempt in range(max_retries):
            try:
                # שליחה ל-API של נטפרי עם verify=False וזמן המתנה ארוך יותר (120 שניות)
                response = requests.post(GEMINI_URL, json=payload, verify=False, timeout=120)
                
                if not response.text:
                    raise Exception("Empty response from Gemini API")
                
                try:
                    response_data = response.json()
                except Exception:
                    raise Exception(f"The API returned a non-JSON response. Raw: {response.text}")
                
                # אם קיבלנו 200 OK, אנחנו יוצאים מהלולאה (הצלחנו!)
                if response.status_code == 200:
                    break
                
                # אם הגענו לכאן, השרת החזיר שגיאה (למשל 503)
                error_msg = response_data.get("error", {}).get("message", "Unknown API Error")
                print(f"API Error Detected on attempt {attempt + 1}: {error_msg}")
                
                # אם זו שגיאת עומס או חריגת קצב, נמתין זמן שהולך וגדל
                if response.status_code in [503, 429] and attempt < max_retries - 1:
                    retry_delay = (attempt + 1) * 3  # השהיה של 3, 6, 9 שניות בהתאמה
                    print(f"Server busy. Retrying in {retry_delay} seconds...")
                    time.sleep(retry_delay)
                    continue # קופץ לניסיון הבא בלולאה
                else:
                    # אם מדובר בשגיאה אחרת (או שנגמרו הניסיונות) זורקים שגיאה החוצה
                    raise HTTPException(status_code=response.status_code, detail=error_msg)
                    
            except Exception as e:
                # תפיסת שגיאות רשת שאינן קשורות לתוכן ה-HTTP, ומנסה שוב עם השהיה מתגברת
                if attempt < max_retries - 1 and not isinstance(e, HTTPException):
                    retry_delay = (attempt + 1) * 3
                    print(f"Request failed (attempt {attempt + 1}): {str(e)}. Retrying in {retry_delay}s...")
                    time.sleep(retry_delay)
                else:
                    if isinstance(e, HTTPException):
                        raise e
                    raise HTTPException(status_code=500, detail=str(e))

        # שליפת הטקסט מהתגובה של גוגל
        try:
            ai_text = response_data['candidates'][0]['content']['parts'][0]['text']
            print(f"AI Response: {ai_text[:50]}...")
            return {"response": ai_text}
        except (KeyError, IndexError):
            print(f"Unexpected JSON structure: {response_data}")
            raise HTTPException(status_code=500, detail="Failed to parse AI response content")

    except HTTPException as he:
        raise he
    except Exception as e:
        print(f"SERVER ERROR: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


# --- תוספות עבור הדאשבורד (main.py) ---

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
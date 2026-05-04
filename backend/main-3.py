
import os
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
# שים לב: השתמשנו בגרסה 1.5-flash שהיא הגרסה היציבה והנתמכת ביותר כרגע
API_KEY = os.getenv("GOOGLE_API_KEY")

#GEMINI_URL = f"https://generativelanguage.googleapis.com/v1/models/gemini-2.5-flash:generateContent?key={API_KEY}"
GEMINI_URL = f"https://generativelanguage.googleapis.com/v1/models/gemini-2.5-flash:generateContent?key={API_KEY}"
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
            # המרה בין הפורמט של הפרונטנד (user/assistant) לפורמט של גוגל (user/model)
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

        # שליחה ל-API של נטפרי
        # verify=False הכרחי בנטפרי כדי למנוע שגיאות תעודת אבטחה ב-Python
        response = requests.post(GEMINI_URL, json=payload, verify=False, timeout=90)

        # בדיקה אם קיבלנו תוכן כלשהו
        if not response.text:
            raise HTTPException(status_code=500, detail="Empty response from Gemini API")

        # ניסיון פענוח ה-JSON - כאן היתה השגיאה המקורית שלך
        try:
            response_data = response.json()
        except Exception:
            print(f"Raw Response (Not JSON): {response.text}")
            raise HTTPException(status_code=500, detail="The API returned a non-JSON response. It might be a NetFree block page.")

        # בדיקה אם ה-API החזיר שגיאה רשמית
        if response.status_code != 200:
            error_msg = response_data.get("error", {}).get("message", "Unknown API Error")
            print(f"API Error Detected: {error_msg}")
            raise HTTPException(status_code=response.status_code, detail=error_msg)

        # שליפת הטקסט מהתגובה של גוגל
        try:
            ai_text = response_data['candidates'][0]['content']['parts'][0]['text']
            print(f"AI Response: {ai_text[:50]}...")
            return {"response": ai_text}
        except (KeyError, IndexError):
            print(f"Unexpected JSON structure: {response_data}")
            raise HTTPException(status_code=500, detail="Failed to parse AI response content")

    except Exception as e:
        print(f"SERVER ERROR: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

        # --- תוספות עבור הדאשבורד (main.py) ---

# רשימות זמניות לשמירת נתונים (במערכת אמיתית נחבר למסד נתונים)
feedbacks_db = []
topics_db = []

# מודלים של Pydantic לקבלת נתונים
class FeedbackRequest(BaseModel):
    agent_name: str
    simulation_topic: str
    score: int
    feedback_text: str
    ai_json_summary: dict = None

class TopicRequest(BaseModel):
    title: str
    prompt_instructions: str

# אנדפוינט לקבלת כל המשובים (עבור הדאשבורד)
@app.get("/api/feedbacks")
async def get_feedbacks():
    return {"feedbacks": feedbacks_db}

# אנדפוינט לשמירת משוב חדש (נקרא בסיום שיחה)
@app.post("/api/feedbacks")
async def save_feedback(feedback: FeedbackRequest):
    feedbacks_db.append(feedback.model_dump())
    return {"status": "success", "message": "Feedback saved"}

# אנדפוינט לקבלת נושאי הסימולציה
@app.get("/api/topics")
async def get_topics():
    return {"topics": topics_db}

# אנדפוינט להוספת נושא חדש על ידי המדריך
@app.post("/api/topics")
async def add_topic(topic: TopicRequest):
    topics_db.append(topic.model_dump())
    return {"status": "success", "message": "Topic added"}

if __name__ == "__main__":
    import uvicorn
    # הרצה על פורט 8000
    uvicorn.run(app, host="0.0.0.0", port=8000)
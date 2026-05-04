import streamlit as st
import requests
import pandas as pd

# הגדרת כתובת ה-API של main.py
API_BASE_URL = "http://localhost:8000/api"

# הגדרות עמוד הדאשבורד
st.set_page_config(page_title="דאשבורד מדריך - סימולטור שירות", layout="wide", page_icon="🎯")

st.title("🎯 דאשבורד הדרכה - ניהול סימולציות")
st.markdown("כאן תוכל לצפות במשובים של הנציגים ולהגדיר נושאי סימולציה חדשים.")

# יצירת טאבים להפרדה בין צפייה במשובים להוספת נושאים
tab_feedbacks, tab_topics = st.tabs(["📊 משובים מסימולציות", "⚙️ ניהול נושאי סימולציה"])

# ==========================================
# טאב 1: הצגת משובים
# ==========================================
with tab_feedbacks:
    st.header("ביצועי הנציגים (משוב מה-AI)")
    
    # כפתור רענון נתונים
    if st.button("🔄 רענן משובים"):
        st.rerun()

    try:
        # קריאה ל-main.py למשיכת המשובים
        response = requests.get(f"{API_BASE_URL}/feedbacks")
        if response.status_code == 200:
            feedbacks = response.json().get("feedbacks", [])
            
            if feedbacks:
                # המרת הנתונים ל-DataFrame של Pandas לתצוגת טבלה נוחה
                df = pd.DataFrame(feedbacks)
                # שינוי שמות העמודות לעברית
                df = df.rename(columns={
                    "agent_name": "שם הנציג",
                    "simulation_topic": "נושא הסימולציה",
                    "score": "ציון",
                    "feedback_text": "פירוט משוב"
                })
                
                # הצגת הטבלה
                st.dataframe(df[["שם הנציג", "נושא הסימולציה", "ציון", "פירוט משוב"]], use_container_width=True)
                
                # חישוב ממוצע ציונים כללי
                avg_score = df["ציון"].mean()
                st.metric("ממוצע ציונים מערכתי", f"{avg_score:.1f}/100")
            else:
                st.info("עדיין אין משובים במערכת. הנציגים צריכים לסיים שיחות כדי שהנתונים יופיעו כאן.")
        else:
            st.error("שגיאה בקבלת נתונים מהשרת.")
    except requests.exceptions.ConnectionError:
        st.error("לא ניתן להתחבר לשרת ה-Backend. ודא ש-main.py פועל ברקע (פורט 8000).")


# ==========================================
# טאב 2: ניהול נושאי סימולציה
# ==========================================
with tab_topics:
    st.header("הוספת נושא סימולציה חדש")
    
    # טופס הזנת נושא חדש
    with st.form("add_topic_form", clear_on_submit=True):
        col1, col2 = st.columns([1, 2])
        with col1:
            title = st.text_input("שם הנושא (לדוגמה: ביטול פוליסת רכב)")
        with col2:
            prompt_instructions = st.text_area("הוראות ל-AI (System Prompt לפונקציה זו)", height=150, 
                                             placeholder="לדוגמה: אתה לקוח עצבני שרוצה לבטל פוליסה בגלל מחיר יקר. עליך לבקש הנחה...")
            
        submit_button = st.form_submit_button("➕ הוסף נושא למערכת")
        
        if submit_button:
            if title and prompt_instructions:
                try:
                    # שליחת הנושא ל-main.py
                    res = requests.post(f"{API_BASE_URL}/topics", json={
                        "title": title,
                        "prompt_instructions": prompt_instructions
                    })
                    if res.status_code == 200:
                        st.success(f"הנושא '{title}' נוסף בהצלחה!")
                    else:
                        st.error("אירעה שגיאה בשמירת הנושא.")
                except Exception as e:
                    st.error(f"שגיאת תקשורת: {e}")
            else:
                st.warning("נא למלא את כל השדות.")

    st.divider()
    
    # הצגת הנושאים הקיימים
    st.subheader("נושאים פעילים במערכת:")
    try:
        res_topics = requests.get(f"{API_BASE_URL}/topics")
        if res_topics.status_code == 200:
            topics = res_topics.json().get("topics", [])
            if topics:
                for idx, t in enumerate(topics):
                    with st.expander(f"📌 {t['title']}"):
                        st.write("**הוראות (Prompt):**")
                        st.code(t['prompt_instructions'], language="text")
            else:
                st.info("אין כרגע נושאים מותאמים אישית.")
    except:
         st.error("לא ניתן לטעון את רשימת הנושאים.")
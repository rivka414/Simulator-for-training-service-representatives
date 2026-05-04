import React, { useState, useEffect } from 'react';
// import './Dashboard.css'; // אופציונלי: קובץ עיצוב

// --- הגדרת הטיפוסים (Interfaces) עבור TypeScript ---
interface IFeedback {
  agent_name: string;
  simulation_topic: string;
  score: number;
  feedback_text: string;
}

interface ITopic {
  title: string;
  prompt_instructions: string;
}

const Dashboard: React.FC = () => {
  // ניהול מצב (State) עם טיפוסים מוגדרים
  const [feedbacks, setFeedbacks] = useState<IFeedback[]>([]);
  const [topics, setTopics] = useState<ITopic[]>([]);
  const [newTopicTitle, setNewTopicTitle] = useState<string>("");
  const [newTopicPrompt, setNewTopicPrompt] = useState<string>("");

  const API_BASE_URL = "http://localhost:8000/api";

  // משיכת הנתונים מהשרת
  const fetchData = async (): Promise<void> => {
    try {
      const [feedbacksRes, topicsRes] = await Promise.all([
        fetch(`${API_BASE_URL}/feedbacks`),
        fetch(`${API_BASE_URL}/topics`)
      ]);
      
      const feedbacksData = await feedbacksRes.json();
      const topicsData = await topicsRes.json();

      setFeedbacks(feedbacksData.feedbacks || []);
      setTopics(topicsData.topics || []);
    } catch (error) {
      console.error("Error fetching data:", error);
    }
  };

  // הפעלה ראשונית של משיכת הנתונים
  useEffect(() => {
    fetchData();
  }, []);

  // פונקציה להוספת נושא חדש - הוספנו טיפוס מתאים ל-Event של הטופס
  const handleAddTopic = async (e: React.FormEvent<HTMLFormElement>): Promise<void> => {
    e.preventDefault();
    if (!newTopicTitle || !newTopicPrompt) return;

    try {
      await fetch(`${API_BASE_URL}/topics`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          title: newTopicTitle,
          prompt_instructions: newTopicPrompt
        })
      });
      
      // איפוס הטופס ורענון רשימת הנושאים
      setNewTopicTitle("");
      setNewTopicPrompt("");
      fetchData(); 
      alert("הנושא נוסף בהצלחה!");
    } catch (error) {
      console.error("Error adding topic:", error);
    }
  };

  return (
    <div style={{ padding: '20px', direction: 'rtl', fontFamily: 'Arial' }}>
      <h1>🎯 דאשבורד מדריך - סימולטור שירות</h1>

      {/* אזור הוספת נושא לסימולציה */}
      <section style={{ marginBottom: '40px', border: '1px solid #ccc', padding: '20px' }}>
        <h2>➕ הוספת נושא סימולציה חדש</h2>
        <form onSubmit={handleAddTopic} style={{ display: 'flex', flexDirection: 'column', gap: '10px', maxWidth: '400px' }}>
          <input 
            type="text" 
            placeholder="שם הנושא (לדוגמה: ביטול פוליסה)" 
            value={newTopicTitle}
            onChange={(e: React.ChangeEvent<HTMLInputElement>) => setNewTopicTitle(e.target.value)}
            required
          />
          <textarea 
            placeholder="הוראות ל-AI (System Prompt)..." 
            value={newTopicPrompt}
            onChange={(e: React.ChangeEvent<HTMLTextAreaElement>) => setNewTopicPrompt(e.target.value)}
            rows={4}
            required
          />
          <button type="submit" style={{ padding: '10px', cursor: 'pointer' }}>הוסף נושא למערכת</button>
        </form>
      </section>

      {/* אזור צפייה במשובים משיחות קודמות */}
      <section>
        <h2>📊 משובים אחרונים מסימולציות</h2>
        <button onClick={fetchData} style={{ marginBottom: '10px' }}>🔄 רענן נתונים</button>
        
        {feedbacks.length === 0 ? (
          <p>אין עדיין משובים במערכת.</p>
        ) : (
          <table style={{ width: '100%', borderCollapse: 'collapse', textAlign: 'right' }}>
            <thead>
              <tr style={{ backgroundColor: '#f2f2f2' }}>
                <th style={{ border: '1px solid #ddd', padding: '8px' }}>שם הנציג</th>
                <th style={{ border: '1px solid #ddd', padding: '8px' }}>נושא הסימולציה</th>
                <th style={{ border: '1px solid #ddd', padding: '8px' }}>ציון</th>
                <th style={{ border: '1px solid #ddd', padding: '8px' }}>פירוט משוב</th>
              </tr>
            </thead>
            <tbody>
              {feedbacks.map((fb, index) => (
                <tr key={index}>
                  <td style={{ border: '1px solid #ddd', padding: '8px' }}>{fb.agent_name}</td>
                  <td style={{ border: '1px solid #ddd', padding: '8px' }}>{fb.simulation_topic}</td>
                  <td style={{ border: '1px solid #ddd', padding: '8px' }}>{fb.score}</td>
                  <td style={{ border: '1px solid #ddd', padding: '8px' }}>{fb.feedback_text}</td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </section>
    </div>
  );
};

export default Dashboard;
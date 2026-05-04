import React, { useState, useEffect, useRef } from 'react';
import { Container, Box, TextField, Typography, Paper, List, ListItem, ListItemText, Button, CircularProgress } from '@mui/material';
import { sendMessageToAI } from './api';

interface Message {
  role: 'user' | 'assistant';
  content: string;
}

const Chat: React.FC = () => {
  const [messages, setMessages] = useState<Message[]>([]);
  const [inputText, setInputText] = useState('');
  const [isTyping, setIsTyping] = useState(false);
  const [isFinished, setIsFinished] = useState(false);
  const [loading, setLoading] = useState(false);
  
  // In the browser, `setTimeout` returns a number (not NodeJS.Timeout).
  const timerRef = useRef<ReturnType<typeof setTimeout> | null>(null);

  // פונקציית שליחת ההודעה - שימו לב שהיא מוגדרת כ-async!
// פונקציית שליחת ההודעה - מעודכנת
// פונקציית שליחת ההודעה המעודכנת
const handleSend = async (textToSend: string, finished: boolean = false) => {
  // הגנה: אם אין טקסט וזה לא סיום שיחה, אל תעשה כלום
  if (!textToSend.trim() && !finished) return;

  // ביטול הטיימר הקיים כדי למנוע כפילויות בשליחה
  if (timerRef.current) clearTimeout(timerRef.current);

  const newMessages: Message[] = [...messages];
  
  if (textToSend.trim()) {
    newMessages.push({ role: 'user', content: textToSend });
    setMessages(newMessages);
    setInputText(''); // איפוס מידי כדי למנוע כפילות
  }
  
  setLoading(true);
  
  try {
    // שליחה ל-AI
    const aiResponse = await sendMessageToAI(newMessages, finished);
    
    // הוספת תשובת ה-AI למסך
    const updatedMessages: Message[] = [...newMessages, { role: 'assistant', content: aiResponse }];
    setMessages(updatedMessages);
    
    if (finished) {
      setIsFinished(true);
      // שליחת המשוב לדאשבורד
      await fetch("http://localhost:8000/api/feedbacks", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          agent_name: "נציג הדגמה", 
          simulation_topic: "סימולציה כללית", 
          score: 0, 
          feedback_text: aiResponse 
        })
      });
    }
  } catch (error) {
    console.error("Error calling AI:", error);
    // אופציונלי: הצגת הודעת שגיאה למשתמש בממשק
  } finally {
    setLoading(false);
    setIsTyping(false);
  }
};

  // מנגנון זיהוי סיום הקלדה (Debounce)
  useEffect(() => {
    if (inputText.trim() === '' || isFinished) return;

    setIsTyping(true);

    // אם המשתמש מקליד, אנחנו מאפסים את הטיימר הקודם
    if (timerRef.current) clearTimeout(timerRef.current);

    // קובעים טיימר של 2 שניות - אם לא הוקלד כלום, נשלח אוטומטית
    timerRef.current = setTimeout(() => {
      setIsTyping(false);
      handleSend(inputText);
    }, 2000);

    return () => {
      if (timerRef.current) clearTimeout(timerRef.current);
    };
  }, [inputText]);

  return (
    <Container maxWidth="md" sx={{ mt: 4, mb: 4, direction: 'rtl' }}>
      <Typography variant="h4" gutterBottom align="center" sx={{ fontWeight: 'bold', color: '#1976d2' }}>
        סימולטור הכשרת נציגים - ביטוח ישיר
      </Typography>

      <Paper elevation={3} sx={{ height: '60vh', overflowY: 'auto', p: 2, mb: 2, backgroundColor: '#f5f5f5' }}>
        <List>
          {messages.map((msg, index) => (
            <ListItem key={index} sx={{ justifyContent: msg.role === 'user' ? 'flex-end' : 'flex-start' }}>
              <Paper sx={{ 
                p: 1.5, 
                backgroundColor: msg.role === 'user' ? '#e3f2fd' : '#ffffff',
                borderRadius: msg.role === 'user' ? '15px 15px 0 15px' : '15px 15px 15px 0',
                maxWidth: '70%'
              }}>
                <ListItemText primary={msg.content} sx={{ textAlign: 'right' }} />
              </Paper>
            </ListItem>
          ))}
          {loading && <CircularProgress size={24} sx={{ m: 2 }} />}
        </List>
      </Paper>

      {!isFinished ? (
        <Box sx={{ display: 'flex', flexDirection: 'column', gap: 2 }}>
          <TextField
            fullWidth
            variant="outlined"
            placeholder="הקלד את תשובת הנציג כאן... (התשובה תישלח אוטומטית לאחר 2 שניות של שקט)"
            value={inputText}
            onChange={(e) => setInputText(e.target.value)}
            disabled={loading}
            multiline
            rows={2}
            sx={{
              '& .MuiInputBase-input': { textAlign: 'right', direction: 'rtl' },
            }}
          />
          <Typography variant="caption" color="textSecondary" sx={{ textAlign: 'right' }}>
            {isTyping ? "הלקוח ממתין שתסיים לדבר..." : "מצב: מוכן לשמוע"}
          </Typography>
          
          <Button 
            variant="contained" 
            color="error" 
            onClick={() => handleSend(inputText, true)}
            disabled={loading}
          >
            סיום שיחה וקבלת משוב
          </Button>
        </Box>
      ) : (
        <Button variant="outlined" onClick={() => window.location.reload()}>שיחה חדשה</Button>
      )}
    </Container>
  );
};

export default Chat;
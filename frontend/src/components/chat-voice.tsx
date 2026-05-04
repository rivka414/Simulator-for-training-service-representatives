import React, { useState, useEffect, useRef } from 'react';
import { Container, Box, TextField, Typography, Paper, List, ListItem, ListItemText, Button, CircularProgress, IconButton } from '@mui/material';
import MicIcon from '@mui/icons-material/Mic';
import MicOffIcon from '@mui/icons-material/MicOff';
import { sendMessageToAI } from './api';

interface Message {
  role: 'user' | 'assistant';
  content: string;
}

const ChatVoice: React.FC = () => {
  const [messages, setMessages] = useState<Message[]>([]);
  const [inputText, setInputText] = useState('');
  const [isFinished, setIsFinished] = useState(false);
  const [loading, setLoading] = useState(false);
  const [isListening, setIsListening] = useState(false);
  
  const recognitionRef = useRef<any>(null);
  const isFinishedRef = useRef(false); // Ref כדי לעקוב אחרי מצב סיום בתוך callbacks

  useEffect(() => {
    const SpeechRecognition = (window as any).SpeechRecognition || (window as any).webkitSpeechRecognition;
    if (SpeechRecognition) {
      recognitionRef.current = new SpeechRecognition();
      recognitionRef.current.lang = 'he-IL';
      // continuous: false גורם לו לעצור ולשלוח ברגע שיש שקט
      recognitionRef.current.continuous = false;
      recognitionRef.current.interimResults = false;

      recognitionRef.current.onresult = (event: any) => {
        const transcript = event.results[0][0].transcript;
        if (transcript.trim()) {
          setInputText(transcript);
          handleSend(transcript);
        }
      };

      recognitionRef.current.onend = () => {
        // אם לא סיימנו את השיחה וה-AI לא "חושב", נחזיר את הסטייט ל-false
        // המיקרופון יפתח שוב אוטומטית רק בסוף השמעת האודיו
        setIsListening(false);
      };
    }
  }, [messages]);

  const toggleListening = () => {
    if (isListening) {
      recognitionRef.current?.stop();
    } else {
      setInputText('');
      recognitionRef.current?.start();
      setIsListening(true);
    }
  };

  const playAudioResponse = async (text: string) => {
    try {
      const cleanText = text.replace(/[*#_]/g, '');
      const response = await fetch('http://localhost:8000/tts', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ text: cleanText }),
      });

      if (!response.ok) throw new Error('TTS request failed');

      const blob = await response.blob();
      const audioUrl = URL.createObjectURL(blob);
      const audio = new Audio(audioUrl);

      audio.onended = () => {
        URL.revokeObjectURL(audioUrl);
        // אם השיחה לא נגמרה, פתח מיקרופון אוטומטית ללקוח
        if (!isFinishedRef.current) {
          recognitionRef.current?.start();
          setIsListening(true);
        }
      };

      await audio.play();
    } catch (error) {
      console.error("שגיאה בהשמעת אודיו:", error);
    }
  };

  const handleSend = async (textToSend: string, finished: boolean = false) => {
    if (!textToSend.trim() && !finished) return;

    if (finished) isFinishedRef.current = true;

    const newMessages: Message[] = [...messages, { role: 'user', content: textToSend }];
    if (!finished) setMessages(newMessages);
    
    setLoading(true);
    // ברגע ששולחים, המיקרופון כבוי עד שה-AI יסיים
    recognitionRef.current?.stop();
    setIsListening(false);
    
    try {
      const aiResponse = await sendMessageToAI(newMessages, finished);
      setMessages(prev => [...prev, { role: 'assistant', content: aiResponse }]);
      
      if (!finished) {
        await playAudioResponse(aiResponse);
      } else {
        setIsFinished(true);
      }
    } catch (error) {
      console.error("Error calling AI:", error);
      
      // טיפול אלגנטי בשגיאות עומס (503) מול גוגל
      if (finished) {
        setMessages(prev => [...prev, { 
          role: 'assistant', 
          content: 'השיחה הסתיימה בהצלחה! עקב עומס חריג בשרתי גוגל לא הצלחנו להפיק את המשוב המפורט כרגע, אבל כל הכבוד על התרגול.' 
        }]);
        setIsFinished(true);
      } else {
        setMessages(prev => [...prev, { 
          role: 'assistant', 
          content: 'סליחה, הרשת קצת עמוסה כרגע. תוכל לחזור על המשפט האחרון?' 
        }]);
        if (!isFinishedRef.current) {
            recognitionRef.current?.start();
            setIsListening(true);
        }
      }
    } finally {
      setLoading(false);
      if (!finished) setInputText('');
    }
  };

  return (
    <Container maxWidth="md" sx={{ mt: 4, mb: 4, direction: 'rtl' }}>
      <Typography variant="h4" gutterBottom align="center" sx={{ fontWeight: 'bold', color: '#1976d2' }}>
        סימולטור קולי - ביטוח ישיר
      </Typography>

      <Paper elevation={3} sx={{ height: '50vh', overflowY: 'auto', p: 2, mb: 2, backgroundColor: '#f5f5f5' }}>
        <List>
          {messages.map((msg, index) => (
            <ListItem key={index} sx={{ justifyContent: msg.role === 'user' ? 'flex-end' : 'flex-start' }}>
              <Paper sx={{ 
                p: 1.5, 
                backgroundColor: msg.role === 'user' ? '#e3f2fd' : '#ffffff',
                borderRadius: msg.role === 'user' ? '15px 15px 0 15px' : '15px 15px 15px 0',
                maxWidth: '75%'
              }}>
                <ListItemText primary={msg.content} />
              </Paper>
            </ListItem>
          ))}
          {loading && (
            <Box sx={{ display: 'flex', justifyContent: 'center', p: 2 }}>
              <CircularProgress size={24} />
            </Box>
          )}
        </List>
      </Paper>

      {!isFinished ? (
        <Box sx={{ display: 'flex', flexDirection: 'column', alignItems: 'center', gap: 2 }}>
          <IconButton 
            color={isListening ? "error" : "primary"} 
            onClick={toggleListening}
            disabled={loading}
            sx={{ 
                width: 100, 
                height: 100, 
                backgroundColor: isListening ? '#ffcdd2' : '#e3f2fd',
                '&:hover': { backgroundColor: isListening ? '#ef9a9a' : '#bbdefb' },
                transition: 'all 0.3s'
            }}
          >
            {isListening ? <MicOffIcon sx={{ fontSize: 50 }} /> : <MicIcon sx={{ fontSize: 50 }} />}
          </IconButton>
          
          <Typography variant="h6" color={isListening ? "error" : "textSecondary"}>
            {isListening ? "הלקוח מקשיב... דברי איתו" : loading ? "ישראל חושב..." : "לחצי על המיקרופון כדי להתחיל"}
          </Typography>

          <TextField
            fullWidth
            variant="outlined"
            placeholder="הטקסט שדיברת יופיע כאן..."
            value={inputText}
            disabled={true} 
            multiline
            rows={2}
          />
          
          <Button 
            fullWidth
            variant="contained" 
            color="error" 
            size="large"
            onClick={() => handleSend(inputText, true)}
            disabled={loading}
            sx={{ fontWeight: 'bold', py: 1.5 }}
          >
            סיום שיחה וקבלת משוב
          </Button>
        </Box>
      ) : (
        <Paper elevation={3} sx={{ p: 4, textAlign: 'center', backgroundColor: '#fff9c4' }}>
            <Typography variant="h5" gutterBottom>הסימולציה הסתיימה!</Typography>
            <Typography variant="body1" sx={{ mb: 3 }}>המשוב שלך מוכן ברשימת ההודעות למעלה.</Typography>
            <Button fullWidth variant="contained" size="large" onClick={() => window.location.reload()}>שיחה חדשה</Button>
        </Paper>
      )}
    </Container>
  );
};

export default ChatVoice;
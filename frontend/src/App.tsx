



import React from 'react';
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import Home from './components/Home';
import Chat from './components/chat';
import Dashboard from './components/dashboard';
import ChatVoice from './components/chat-voice';

const App: React.FC = () => {
  return (
    <Router>
      <div style={{ direction: 'rtl', fontFamily: 'Arial, sans-serif' }}>
        <Routes>
          <Route path="/" element={<Home />} />
          <Route path="/chat" element={<Chat />} />
          <Route path="/dashboard" element={<Dashboard />} />
          <Route path="/chat-voice" element={<ChatVoice />} /> {/* נתיב חדש לשיחה קולית */}
        </Routes>
      </div>
    </Router>
  );
};

export default App;
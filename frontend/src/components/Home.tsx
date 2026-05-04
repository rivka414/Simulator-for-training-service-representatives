import React from 'react';
import { useNavigate } from 'react-router-dom';

const Home: React.FC = () => {
  const navigate = useNavigate();

  const containerStyle: React.CSSProperties = {
    display: 'flex',
    flexDirection: 'column',
    alignItems: 'center',
    justifyContent: 'center',
    height: '100vh',
    backgroundColor: '#f4f7f6',
    gap: '20px'
  };

  const cardContainerStyle: React.CSSProperties = {
    display: 'flex',
    gap: '30px',
  };

  const cardStyle: React.CSSProperties = {
    width: '250px',
    padding: '40px',
    textAlign: 'center',
    backgroundColor: 'white',
    borderRadius: '15px',
    boxShadow: '0 4px 15px rgba(0,0,0,0.1)',
    cursor: 'pointer',
    transition: 'transform 0.2s',
  };

  return (
    <div style={containerStyle}>
      <h1 style={{ color: '#333', marginBottom: '30px' }}>סימולטור הכשרת נציגי שירות</h1>
      <p style={{ fontSize: '1.2rem', color: '#666' }}>בחר את התפקיד שלך כדי להתחיל:</p>
      
      <div style={cardContainerStyle}>



        {/* כרטיס נציג */}
        <div 
          style={cardStyle} 
          onClick={() => navigate('/chat-voice')}
          onMouseEnter={(e) => e.currentTarget.style.transform = 'scale(1.05)'}
          onMouseLeave={(e) => e.currentTarget.style.transform = 'scale(1)'}
        >
          <div style={{ fontSize: '3rem', marginBottom: '10px' }}>🎧</div>
          <h2 style={{ color: '#007bff' }}>כניסת לסימולציה</h2>
          <p>התחל סימולציית צ'אט עם לקוח וירטואלי</p>
        </div>

        {/* כרטיס מדריך */}
        <div 
          style={cardStyle} 
          onClick={() => navigate('/dashboard')}
          onMouseEnter={(e) => e.currentTarget.style.transform = 'scale(1.05)'}
          onMouseLeave={(e) => e.currentTarget.style.transform = 'scale(1)'}
        >
          <div style={{ fontSize: '3rem', marginBottom: '10px' }}>📊</div>
          <h2 style={{ color: '#28a745' }}>כניסת מדריך</h2>
          <p>ניהול נושאי סימולציה וצפייה במשובים</p>
        </div>
      </div>
    </div>
  );
};

export default Home;
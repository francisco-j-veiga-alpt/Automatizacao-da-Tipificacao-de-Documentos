// App.tsx
import React from 'react';
import { BrowserRouter as Router, Route, Routes } from 'react-router-dom';
import Dashboard from './pages/Dashboard';
import PortalQueixa from './pages/PortalDaQeixa';
import QualChatbot from './pages/QualtricsChatbot';
import NavBar from './components/NavBar';
import './index.css';

const App: React.FC = () => {
  return (
      <Router>
          <NavBar />
          <Routes>
              <Route path="/" element={<Dashboard />} />
              <Route path="/portal-da-queixa" element={<PortalQueixa />} />
              <Route path="/qualtrics-chatbot" element={<QualChatbot />} />
          </Routes>
      </Router>
  );
};

export default App;
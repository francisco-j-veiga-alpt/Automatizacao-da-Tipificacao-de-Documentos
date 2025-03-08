// App.tsx

import React from 'react';
import { BrowserRouter as Router, Route, Routes } from 'react-router-dom';
import Dashboard from './pages/Dashboard';
import PortalDaQeixa from './pages/PortalDaQeixa';
import QualtricsChatbot from './pages/QualtricsChatbot';
import NavBar from './components/NavBar';

const App: React.FC = () => {
  return (
    <Router>
      <NavBar />
      <Routes>
        <Route path="/dashboard" element={<Dashboard />} />
        <Route path="/portal-da-queixa" element={<PortalDaQeixa />} />
        <Route path="/qualtrics-chatbot" element={<QualtricsChatbot />} />
      </Routes>
    </Router>
  );
};

export default App;

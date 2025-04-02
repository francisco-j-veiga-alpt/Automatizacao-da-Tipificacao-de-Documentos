// App.tsx

import React from 'react';
import { BrowserRouter as Router, Route, Routes } from 'react-router-dom';
import PortalDaQeixa from './pages/PortalDaQeixa';
import NavBar from './components/NavBar';

const App: React.FC = () => {
  return (
    <Router>
      <NavBar />
      <Routes>
        {/* <Route path="/dashboard" element={<Dashboard />} />
        <Route path="/qualtrics-chatbot" element={<QualtricsChatbot />} />
        <Route path="/cliente-misterio" element={<ClienteMisterio />} /> */}

        <Route path="/portal-da-queixa" element={<PortalDaQeixa />} />
      </Routes>
    </Router>
  );
};

export default App;

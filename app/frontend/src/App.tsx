// App.tsx
import React from 'react';
import { BrowserRouter as Router, Route, Routes } from 'react-router-dom';
import PortalDaQeixa from './pages/PortalDaQeixa';
import NavBar from './components/NavBar';
import AdminTasks from './pages/AdminTasks'; // <<< Import the new page

const App: React.FC = () => {
  return (
    <Router>
      <NavBar />
      <Routes>
        {/* Keep existing routes */}
        <Route path="/portal-da-queixa" element={<PortalDaQeixa />} />
        {/* Add other page routes if they exist */}
        {/* <Route path="/dashboard" element={<Dashboard />} /> */}
        {/* <Route path="/qualtrics-chatbot" element={<QualtricsChatbot />} /> */}
        {/* <Route path="/cliente-misterio" element={<ClienteMisterio />} /> */}

        {/* >>> Add Route for Admin Page <<< */}
        <Route path="/admin" element={<AdminTasks />} />
        {/* >>> END <<< */}

        {/* Optional: Add a default route or redirect */}
         <Route path="/" element={<PortalDaQeixa />} /> {/* Example: default to portal */}

      </Routes>
    </Router>
  );
};

export default App;
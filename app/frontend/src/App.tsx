import React from 'react';
import NavBar from './components/Navbar';

import { BrowserRouter as Router, Route, Routes } from 'react-router-dom';
import ComprasPage from './pages/ComprasPage';
import UsersPage from './pages/UsersPage';

const App: React.FC = () => {
  return (
    <Router>
      <NavBar />
      <Routes>
        <Route path="/" element={<UsersPage />} />
        <Route path="/compras" element={<ComprasPage />} />
      </Routes>
    </Router>
  );
};

export default App;

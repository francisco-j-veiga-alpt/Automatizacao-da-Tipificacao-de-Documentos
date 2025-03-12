// NavBar.tsx

import React from 'react';
import { Link } from 'react-router-dom';

const NavBar: React.FC = () => {
  return (
    <nav className="navbar">
      <ul className="nav-links">
        <li><Link to="/dashboard">Dashboard</Link></li>
        <li><Link to="/portal-da-queixa">Portal da Queixa</Link></li>
        <li><Link to="/qualtrics-chatbot">Qualtrics Chatbot</Link></li>
        <li><Link to="/cliente-misterio">Cliente Misterio</Link></li>
      </ul>
    </nav>
  );
};

export default NavBar;

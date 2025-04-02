// NavBar.tsx

import React from 'react';
import { Link } from 'react-router-dom';

const NavBar: React.FC = () => {
  return (
    <nav className="navbar">
      <ul className="nav-links">
        <li><Link to="/portal-da-queixa">Portal da Queixa</Link></li>
      </ul>
    </nav>
  );
};

export default NavBar;

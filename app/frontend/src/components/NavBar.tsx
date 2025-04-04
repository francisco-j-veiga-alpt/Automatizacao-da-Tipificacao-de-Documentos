// NavBar.tsx
import React from 'react';
import { Link } from 'react-router-dom';

const NavBar: React.FC = () => {
  return (
    <nav className="navbar">
      <ul className="nav-links">
        {/* Keep existing links */}
        <li><Link to="/portal-da-queixa">Portal da Queixa</Link></li>
        {/* Add other links if they exist */}
        {/* <li><Link to="/dashboard">Dashboard</Link></li> */}

        {/* >>> Add Link to Admin Page <<< */}
        <li><Link to="/admin">Admin Tasks</Link></li>
        {/* >>> END <<< */}
      </ul>
    </nav>
  );
};

export default NavBar;
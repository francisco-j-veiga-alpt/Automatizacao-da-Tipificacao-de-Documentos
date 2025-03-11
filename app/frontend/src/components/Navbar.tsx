// /components/Navbar.tsx
import React from 'react';
import { Link } from 'react-router-dom';

const Navbar: React.FC = () => {
    return (
        <nav className="navbar">
            <Link to="/" className="navbar-link">Users</Link>
            <Link to="/compras" className="navbar-link">Compras</Link>
        </nav>
    );
};

export default Navbar;
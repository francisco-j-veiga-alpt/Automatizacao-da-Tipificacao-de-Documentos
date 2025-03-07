import React from 'react';
import { Link } from 'react-router-dom';

const NavBar: React.FC = () => {
    return (
        <nav className="navbar">
            <ul className="nav-links">
                <li>
                    <Link to="/">Dashboard</Link>
                </li>
                <li>
                    <Link to="/portal-da-queixa">Portal da queixa</Link>
                </li>
                <li>
                    <Link to="/qualtrics-chatbot">Qualtrics chatbot</Link>
                </li>
            </ul>
        </nav>
    );
};

export default NavBar;

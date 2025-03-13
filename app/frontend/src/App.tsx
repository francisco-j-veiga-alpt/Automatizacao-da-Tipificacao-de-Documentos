import React from 'react';
import NavBar from './components/Navbar';
import { BrowserRouter as Router, Route, Routes } from 'react-router-dom';
import ComprasPage from './pages/ComprasPage';
import UsersPage from './pages/UsersPage';
import AddUserPage from './pages/AddUserPage';
import HomePage from './pages/HomePage'; // Import HomePage
import DeleteUserPage from './pages/DeleteUserPage'; // Add this import
import EditUserPage from './pages/EditUserPage'; // Import EditUserPage



const App: React.FC = () => {
  return (
    <Router>
      <NavBar />
      <Routes>
        <Route path="/" element={<HomePage />} /> {/* Add HomePage route */}
        <Route path="/users" element={<UsersPage />} />
        <Route path="/compras" element={<ComprasPage />} />
        <Route path="/add-user" element={<AddUserPage />} />
        <Route path="/delete-user" element={<DeleteUserPage />} />
        <Route path="/update-user" element={<EditUserPage />} /> {/* Add the new route */}
      </Routes>
    </Router>
  );
};

export default App;

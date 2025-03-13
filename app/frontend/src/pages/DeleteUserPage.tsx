// src/pages/DeleteUserPage.tsx
import React, { useState } from 'react';

const DeleteUserPage: React.FC = () => {
    const [name, setName] = useState('');
    const [message, setMessage] = useState('');
    const [error, setError] = useState('');

    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault();

        try {
            const response = await fetch('http://localhost:8000/delete-user', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ name }),
            });

            const data = await response.json();

            if (!response.ok) {
                throw new Error(data.error || 'Failed to delete user');
            }

            setMessage(data.message);
            setName('');
            setError('');
        } catch (err) {
            setError(err instanceof Error ? err.message : 'Unknown error occurred');
            setMessage('');
        }
    };

    return (
        <div className="page-container">
            <h1>Delete User</h1>
            <form onSubmit={handleSubmit} className="delete-form">
                <div className="form-group">
                    <label htmlFor="name">User Name:</label>
                    <input
                        type="text"
                        id="name"
                        value={name}
                        onChange={(e) => setName(e.target.value)}
                        required
                    />
                </div>
                <button type="submit" className="delete-button">
                    Delete User
                </button>
            </form>

            {message && <div className="success-message">{message}</div>}
            {error && <div className="error-message">{error}</div>}
        </div>
    );
};

export default DeleteUserPage;

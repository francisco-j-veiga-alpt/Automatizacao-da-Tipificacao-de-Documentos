// src/pages/AddUserPage.tsx
import React, { useState } from 'react';

const AddUserPage: React.FC = () => {
  const [name, setName] = useState('');
  const [age, setAge] = useState('');
  const [city, setCity] = useState('');

  // Marked function as async
  const handleSubmit = async (event: React.FormEvent) => {
    event.preventDefault();

    try {
      const response = await fetch('http://localhost:8000/add-users', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          name: name,
          age: parseInt(age),
          city: city
        }),
      });

      if (!response.ok) {
        throw new Error('Failed to add user');
      }

      // Handle successful response
      const result = await response.json();
      console.log('User added:', result);

    } catch (error) {
      console.error('Error adding user:', error);
    }
  };

  return (
    <div className="add">
      <h1>Add User</h1>
      <form onSubmit={handleSubmit} className="add-user-form">
        <div className="form-group">
          <label htmlFor="name">Name:</label>
          <input
            type="text"
            id="name"
            value={name}
            onChange={(e) => setName(e.target.value)}
            required
          />
        </div>
        <div className="form-group">
          <label htmlFor="age">Age:</label>
          <input
            type="number"
            id="age"
            value={age}
            onChange={(e) => setAge(e.target.value)}
            required
          />
        </div>
        <div className="form-group">
          <label htmlFor="city">City:</label>
          <input
            type="text"
            id="city"
            value={city}
            onChange={(e) => setCity(e.target.value)}
            required
          />
        </div>
        <button type="submit" className="submit-button">
          Add User
        </button>
      </form>
    </div>
  );
};

export default AddUserPage;

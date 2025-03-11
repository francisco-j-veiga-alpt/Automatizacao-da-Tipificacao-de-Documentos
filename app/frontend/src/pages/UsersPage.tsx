// /pages/UsersPage.tsx
import React from 'react';
import useFetchData from '../hooks/useFetchData'; // Import the hook

interface User {
  name: string;
  age: number;
  city: string;
}

const UsersPage: React.FC = () => {
  const { data: users, loading, error } = useFetchData<User>('http://localhost:8000/list-users');

  if (loading) return <div className="loading">Loading...</div>;
  if (error) return <div className="error">Error: {error}</div>;

  return (
    <div className="page-container">
      <h1>Users</h1>
      {users.length === 0 ? (
        <div className="no-data">No users found.</div>
      ) : (
        <ul className="data-list">
          {users.map((item, index) => (
            <li key={index} className="data-item">
              Name: {item.name}, Age: {item.age}, City: {item.city}
            </li>
          ))}
        </ul>
      )}
    </div>
  );
};

export default UsersPage;

// /pages/UsersPage.tsx
import React, { useEffect, useState } from 'react';


interface User {
    name: string;
    age: number;
    city: string;
}

interface ApiResponse {
    list: User[];
}

const UsersPage: React.FC = () => {
    const [data, setData] = useState<User[]>([]);
    const [loading, setLoading] = useState<boolean>(true);
    const [error, setError] = useState<string | null>(null);

    useEffect(() => {
        const fetchData = async () => {
            try {
                const response = await fetch('http://localhost:8000/list-users'); // Replace with your API endpoint
                if (!response.ok) {
                    throw new Error('Network response was not ok');
                }
                const result: ApiResponse = await response.json();
                setData(result.list);
            } catch (error) {
                // Narrow down the type of `error`
                if (error instanceof Error) {
                    setError(error.message); // Access `error.message` safely
                } else {
                    setError('An unknown error occurred'); // Handle non-Error types
                }
            } finally {
                setLoading(false);
            }
        };

        fetchData();
    }, []);

    if (loading) {
        return <div className="loading">Loading...</div>;
    }

    if (error) {
        return <div className="error">Error: {error}</div>;
    }

    return (
        <div className="users-page">
            <h1>Users</h1>
            {data.length === 0 ? (
                <p className="no-users">No users found.</p>
            ) : (
                <ul className="users-list">
                    {data.map((item, index) => (
                        <li key={index} className="user-item">
                            <h2>{item.name}</h2>
                            <p>Age: {item.age}</p>
                            <p>City: {item.city}</p>
                        </li>
                    ))}
                </ul>
            )}
        </div>
    );
};

export default UsersPage;
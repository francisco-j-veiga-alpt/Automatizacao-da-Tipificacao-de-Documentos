// /pages/ComprasPage.tsx
import React, { useEffect, useState } from 'react';


// Define the User interface
interface Compras {
    id_client: number;
    quantidade: number;
    id_produto: number;
}

// Define the API response interface
interface ApiResponse {
    list: Compras[];
}

const ComprasPage: React.FC = () => {
    // State for storing the list of users
    const [data, setData] = useState<Compras[]>([]);

    // State for loading status
    const [loading, setLoading] = useState<boolean>(true);

    // State for error handling
    const [error, setError] = useState<string | null>(null);

    // Fetch data from the API
    useEffect(() => {
        const fetchData = async () => {
            try {
                // Make the API request
                const response = await fetch('http://localhost:8000/list-compras'); // Replace with your API endpoint

                // Check if the response is OK (status code 200-299)
                if (!response.ok) {
                    throw new Error('Network response was not ok');
                }

                // Parse the JSON response
                const result: ApiResponse = await response.json();

                // Update the state with the fetched data
                setData(result.list);
            } catch (error) {
                // Handle errors safely
                if (error instanceof Error) {
                    setError(error.message); // Access `error.message` safely
                } else {
                    setError('An unknown error occurred'); // Handle non-Error types
                }
            } finally {
                // Set loading to false after the request completes
                setLoading(false);
            }
        };

        // Call the fetch function
        fetchData();
    }, []); // Empty dependency array ensures this runs only once on mount

    // Display loading state
    if (loading) {
        return <div className="loading">Loading...</div>;
    }

    // Display error state
    if (error) {
        return <div className="error">Error: {error}</div>;
    }

    // Display the list of users
    return (
        <div className="compras-page">
            <h1>Compras</h1>
            {data.length === 0 ? (
                <p className="no-compras">No compras found.</p>
            ) : (
                <ul className="compras-list">
                    {data.map((item, index) => (
                        <li key={index} className="compras-item">
                            <h2>{item.id_client}</h2>
                            <p>Age: {item.quantidade}</p>
                            <p>City: {item.id_produto}</p>
                        </li>
                    ))}
                </ul>
            )}
        </div>
    );
};

export default ComprasPage;
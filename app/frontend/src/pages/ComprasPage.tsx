// /pages/ComprasPage.tsx
import React from 'react';
import useFetchData from '../hooks/useFetchData'; // Import the hook

interface Compras {
  id_client: number;
  quantidade: number;
  id_produto: number;
}

const ComprasPage: React.FC = () => {
  const { data: compras, loading, error } = useFetchData<Compras>('http://localhost:8000/list-compras');

  if (loading) return <div className="loading">Loading...</div>;
  if (error) return <div className="error">Error: {error}</div>;

  return (
    <div className="page-container">
      <h1>Compras</h1>
      {compras.length === 0 ? (
        <div className="no-data">No compras found.</div>
      ) : (
        <ul className="data-list">
          {compras.map((item) => (
            <li key={`${item.id_client}-${item.id_produto}`} className="data-item">
              Client ID: {item.id_client}, Quantity: {item.quantidade}, Product ID: {item.id_produto}
            </li>
          ))}
        </ul>
      )}
    </div>
  );
};

export default ComprasPage;

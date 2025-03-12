// src/pages/ClienteMisterio.tsx
import React from 'react';
import FileUploader from '../components/FileUploader';

const ClienteMisterio: React.FC = () => {
  return (
    <div className="cliente-misterio">
      <h1>Cliente Misterio - File Upload</h1>
      <FileUploader />
    </div>
  );
};

export default ClienteMisterio;

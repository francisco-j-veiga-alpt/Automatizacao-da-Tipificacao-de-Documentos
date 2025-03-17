// src/pages/ClienteMisterio.tsx
import React from 'react';
import FileUploader from '../components/FileUploader';
import FeedbackTemplate from '../components/FeedbackTemplate';
import ProcessReport from '../components/ProcessReport';

const ClienteMisterio: React.FC = () => {
  return (
    <>
    <FileUploader source="cliente_misterio" />
    <ProcessReport source="cliente_misterio" />
    <FeedbackTemplate
    title="Cliente Misterio - Análise de Feedback"
    source="cliente_misterio"
  />
  </>
  );
};

export default ClienteMisterio;

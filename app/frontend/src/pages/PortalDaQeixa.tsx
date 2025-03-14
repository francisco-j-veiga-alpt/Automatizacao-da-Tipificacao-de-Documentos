// src/pages/PortalDaQeixa.tsx
import React from 'react';
import FeedbackTemplate from '../components/FeedbackTemplate';
import ProcessReport from '../components/ProcessReport';

const PortalDaQeixa: React.FC = () => {
  return (
    <>
    <ProcessReport source="portal_da_queixa" />
    <FeedbackTemplate
      title="Portal da Queixa - Análise de Feedback"
      source="portal_da_queixa"
    />
    </>
  );
};

export default PortalDaQeixa;

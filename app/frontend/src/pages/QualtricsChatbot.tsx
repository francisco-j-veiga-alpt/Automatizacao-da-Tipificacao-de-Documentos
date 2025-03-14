// src/pages/QualtricsChatbot.tsx

import React from 'react';
import FeedbackTemplate from '../components/FeedbackTemplate';
import ProcessReport from '../components/ProcessReport';

const QualtricsChatbot: React.FC = () => {
  return (
    <>
    <ProcessReport source="qualtrics_chatbot" />
    <FeedbackTemplate
      title="Qualtrics Chatbot - Análise de Feedback"
      source="qualtrics_chatbot"
    />
    </>

  );
};

export default QualtricsChatbot;

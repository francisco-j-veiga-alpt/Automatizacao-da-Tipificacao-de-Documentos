// src/pages/PortalDaQeixa.tsx

import React, { useEffect, useState } from 'react';
import { fetchAvailableTimestamps, fetchReportData } from '../services/api';
import FeedbackTemplate from '../components/FeedbackTemplate';
import { FeedbackData } from '../types/feedbackTypes';

const QualtricsChatbot: React.FC = () => {
  const [feedbackData, setFeedbackData] = useState<FeedbackData | null>(null);
  const [timestamps, setTimestamps] = useState<string[]>([]);
  const [selectedTimestamp, setSelectedTimestamp] = useState('');
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const loadTimestamps = async () => {
      try {
        const data = await fetchAvailableTimestamps("qualtrics_chatbot_reports");
        setTimestamps(data);
        if (data.length > 0) {
          setSelectedTimestamp(data[0]);
        }
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Unknown error');
      }
    };
    loadTimestamps();
  }, []);

  useEffect(() => {
    if (!selectedTimestamp) return;

    const [year, month] = selectedTimestamp.split('-');
    const loadReportData = async () => {
      setLoading(true);
      try {
        const data = await fetchReportData("qualtrics_chatbot", year, month);
        setFeedbackData(data);
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Unknown error');
      } finally {
        setLoading(false);
      }
    };
    loadReportData();
  }, [selectedTimestamp]);

  return (
    <FeedbackTemplate
      title="Qualtrics Chatbot - Análise de Reclamações"
      data={feedbackData}
      loading={loading}
      error={error}
      timestamps={timestamps}
      selectedTimestamp={selectedTimestamp}
      onTimestampChange={setSelectedTimestamp}
    />
  );
};

export default QualtricsChatbot;

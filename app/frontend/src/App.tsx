// src/App.tsx
import React, { useState, useEffect } from 'react';
import { Container, Spinner } from 'react-bootstrap';
import Dashboard from './components/Dashboard';
import { FeedbackData } from './types';

const API_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000/feedback/portal-da-queixa/summary';

const App: React.FC = () => {
  const [feedbackData, setFeedbackData] = useState<FeedbackData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const fetchData = async () => {
      setLoading(true);
      try {
        const response = await fetch(API_URL);
        if (!response.ok) {
          throw new Error(`HTTP error! status: ${response.status}`);
        }
        const data: FeedbackData = await response.json();
        setFeedbackData(data);
      } catch (e: any) {
        setError(e.message);
        console.error("Could not fetch data: ", e);
      } finally {
        setLoading(false);
      }
    };

    fetchData();
  }, []);

  if (loading) {
    return (
      <Container className="d-flex justify-content-center align-items-center vh-100">
        <Spinner animation="border" role="status">
          <span className="visually-hidden">Loading...</span>
        </Spinner>
      </Container>
    );
  }

  if (error) {
    return <Container className="text-danger">Error: {error}</Container>;
  }

  if (!feedbackData) {
    return <Container>No data to display.</Container>;
  }

  return (
    <Container>
      <h1>Feedback Dashboard</h1>
      <Dashboard data={feedbackData} />
    </Container>
  );
};

export default App;

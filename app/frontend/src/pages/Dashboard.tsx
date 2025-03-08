// src/pages/Dashboard.tsx

import React, { useEffect, useState } from 'react';
import { fetchDashboardData } from '../services/api';
import { DashboardData } from '../types/dashboardTypes';
import SentimentTrendChart from '../components/SentimentTrendChart';
import AreaTrendChart from '../components/AreaTrendChart';
import TopIssuesChart from '../components/TopIssuesChart';
import '../index.css'; // Import global CSS

const Dashboard: React.FC = () => {
  const [dashboardData, setDashboardData] = useState<DashboardData | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchData = async () => {
      try {
        const data = await fetchDashboardData(3);
        setDashboardData(data);
      } catch (error) {
        setError('Failed to fetch dashboard data. Please try again later.');
      } finally {
        setLoading(false);
      }
    };
    fetchData();
  }, []);

  if (loading) return <div>Loading...</div>;
  if (error) return <div>Error: {error}</div>;
  if (!dashboardData) return <div>No data available</div>;

  return (
    <div className="dashboard-container">
      <h1>Cliente Feedback Dashboard</h1>

      <div className="dashboard-content">
        <div className="dashboard-box">
          <h2>Sentimento do Cliente</h2>
          <SentimentTrendChart data={dashboardData.results_total_by_mont} />
        </div>

        <div className="dashboard-box">
          <h2>Top Área de Feedback</h2>
          <AreaTrendChart data={dashboardData.results_total_by_mont} />
        </div>

        <div className="dashboard-box full-width">
          <h2>Top 10 Assuntos</h2>
          <TopIssuesChart data={dashboardData.results_total_by_mont} />
        </div>
      </div>
    </div>
  );
};

export default Dashboard;

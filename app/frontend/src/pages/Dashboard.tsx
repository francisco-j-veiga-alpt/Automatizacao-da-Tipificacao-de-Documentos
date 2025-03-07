// Dashboard.tsx
import React, { useEffect, useState } from 'react';
import { fetchDashboardData } from '../services/api';
import { DashboardData } from '../types/dashboardTypes';
import SentimentTrendChart from '../components/SentimentTrendChart';
import AreaTrendChart from '../components/AreaTrendChart';
import TopIssuesChart from '../components/TopIssuesChart';
import NavBar from '../components/NavBar';

const Dashboard: React.FC = () => {
    const [dashboardData, setDashboardData] = useState<DashboardData | null>(null);
    const [error, setError] = useState<string | null>(null);

    useEffect(() => {
        const fetchData = async () => {
            try {
                const data = await fetchDashboardData(3);
                setDashboardData(data);
            } catch (error) {
                console.error('Error fetching dashboard data:', error);
                setError('Failed to fetch dashboard data. Please try again later.');
            }
        };

        fetchData();
    }, []);

    if (error) {
        return <div className="dashboard">Error: {error}</div>;
    }

    if (!dashboardData || !dashboardData.results_total_by_mont) {
        return <div className="dashboard">Loading...</div>;
    }

    return (
        <>
            <div className="dashboard"> {/* Added dashboard container */}
                <h1>Cliente Feedback Dashboard</h1>
                <div className="chart-row">
                    <div className="chart-half">
                        <h2>Sentimento do Cliente</h2>
                        <SentimentTrendChart data={dashboardData.results_total_by_mont} />
                    </div>
                    <div className="chart-half">
                        <h2>Área de Feedback</h2>
                        <AreaTrendChart data={dashboardData.results_total_by_mont} />
                    </div>
                </div>
                <div className="chart chart-full">
                    <h2>Top 10 Assunto</h2>
                    <TopIssuesChart data={dashboardData.results_total_by_mont} />
                </div>
            </div> {/* Added dashboard container */}
        </>
    );
};

export default Dashboard;

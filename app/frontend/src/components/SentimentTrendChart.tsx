import React, { useState } from 'react';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts';
import { MonthData } from '../types/dashboardTypes';

interface SentimentTrendChartProps {
  data: MonthData[];
}

const SentimentTrendChart: React.FC<SentimentTrendChartProps> = ({ data }) => {
  const [activeLine, setActiveLine] = useState<string | null>(null); // Track the currently active line or show all

  const chartData = data.map(month => ({
    month: month.yearMonth,
    Positive: month.sentiments.find(s => s.sentiment === "Positivo")?.count || 0,
    Neutral: month.sentiments.find(s => s.sentiment === "Neutro")?.count || 0,
    Negative: month.sentiments.find(s => s.sentiment === "Negativo")?.count || 0,
  }));

  const handleLegendClick = (e: any) => {
    const clickedLine = e.dataKey as string;
    setActiveLine(prevActiveLine => (prevActiveLine === clickedLine ? null : clickedLine)); // Toggle between the clicked line and showing all
  };

  return (
    <ResponsiveContainer width="100%" height={300}>
      <LineChart data={chartData}>
        <CartesianGrid strokeDasharray="3 3" />
        <XAxis dataKey="month" />
        <YAxis />
        <Tooltip />
        <Legend
          onClick={handleLegendClick}
          wrapperStyle={{ fontSize: '14px', cursor: 'pointer' }}
        />
        {(activeLine === null || activeLine === "Positive") && (
          <Line type="monotone" dataKey="Positive" stroke="#28a745" strokeWidth={3} dot={{ r: 4 }} />
        )}
        {(activeLine === null || activeLine === "Neutral") && (
          <Line type="monotone" dataKey="Neutral" stroke="#8884d8" strokeDasharray="5 5" />
        )}
        {(activeLine === null || activeLine === "Negative") && (
          <Line type="monotone" dataKey="Negative" stroke="#FF4D4F" strokeWidth={3} dot={{ r: 4 }} />
        )}
      </LineChart>
    </ResponsiveContainer>
  );
};

export default SentimentTrendChart;

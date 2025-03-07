import React from 'react';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend } from 'recharts';
import { MonthData } from '../types/dashboardTypes';

interface SentimentTrendChartProps {
  data: MonthData[];
}

const SentimentTrendChart: React.FC<SentimentTrendChartProps> = ({ data }) => {
  const chartData = data.map(month => ({
    month: month.yearMonth,
    Positive: month.sentiments.find(s => s.sentiment === "Positivo")?.count || 0,
    Neutral: month.sentiments.find(s => s.sentiment === "Neutro")?.count || 0,
    Negative: month.sentiments.find(s => s.sentiment === "Negativo")?.count || 0,
  }));

  return (
    <LineChart width={600} height={300} data={chartData}>
      <CartesianGrid strokeDasharray="3 3" />
      <XAxis dataKey="month" />
      <YAxis />
      <Tooltip />
      <Legend />
      <Line type="monotone" dataKey="Positive" stroke="#82ca9d" />
      <Line type="monotone" dataKey="Neutral" stroke="#8884d8" />
      <Line type="monotone" dataKey="Negative" stroke="#ff7300" />
    </LineChart>
  );
};

export default SentimentTrendChart;

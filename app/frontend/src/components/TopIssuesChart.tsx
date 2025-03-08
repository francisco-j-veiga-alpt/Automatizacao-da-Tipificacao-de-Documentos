import React from 'react';
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts';
import { MonthData } from '../types/dashboardTypes';

interface TopIssuesChartProps {
  data: MonthData[];
}

const TopIssuesChart: React.FC<TopIssuesChartProps> = ({ data }) => {
  const allIssues = data.flatMap(month =>
    month.sentiments.flatMap(sentiment =>
      sentiment.areas.flatMap(area =>
        area.classificacoes.flatMap(classificacao =>
          classificacao.assuntos.map(assunto => ({
            issue: assunto.assunto,
            count: assunto.count,
          }))
        )
      )
    )
  );

  const aggregatedIssues = allIssues.reduce((acc, curr) => {
    acc[curr.issue] = (acc[curr.issue] || 0) + curr.count;
    return acc;
  }, {} as Record<string, number>);

  const sortedIssues = Object.entries(aggregatedIssues)
    .map(([issue, count]) => ({ issue, count }))
    .sort((a, b) => b.count - a.count)
    .slice(0, 10);

  return (
    <ResponsiveContainer width="100%" height={300}>
      <BarChart data={sortedIssues}>
        <CartesianGrid strokeDasharray="3 3" />
        <XAxis dataKey="issue" angle={-45} textAnchor="end" interval={0} height={100} />
        <YAxis />
        <Tooltip />
        <Legend verticalAlign="top" wrapperStyle={{ fontSize: '14px' }} />
        <Bar dataKey="count" fill="#1FABEB" />
      </BarChart>
    </ResponsiveContainer>
  );
};

export default TopIssuesChart;

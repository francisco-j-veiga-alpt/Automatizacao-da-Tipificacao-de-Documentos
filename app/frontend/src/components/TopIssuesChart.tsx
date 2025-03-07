import React from 'react';
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend } from 'recharts';
import { MonthData } from '../types/dashboardTypes';

interface TopIssuesChartProps {
  data: MonthData[];
}

const TopIssuesChart: React.FC<TopIssuesChartProps> = ({ data }) => {
  const allIssues = data.flatMap(month => 
    month.sentiments[0].areas.flatMap(area => 
      area.classificacoes.flatMap(classificacao => 
        classificacao.assuntos.map(assunto => ({
          issue: assunto.assunto,
          count: assunto.count
        }))
      )
    )
  );

  const aggregatedIssues = allIssues.reduce((acc, curr) => {
    acc[curr.issue] = (acc[curr.issue] || 0) + curr.count;
    return acc;
  }, {} as Record<string, number>);

  const sortedIssues = Object.entries(aggregatedIssues)
    .sort(([, a], [, b]) => b - a)
    .slice(0, 10)
    .map(([issue, count]) => ({ issue, count }));

  return (
    <BarChart width={600} height={300} data={sortedIssues}>
      <CartesianGrid strokeDasharray="3 3" />
      <XAxis dataKey="issue" angle={-45} textAnchor="end" interval={0} height={100} />
      <YAxis />
      <Tooltip />
      <Legend />
      <Bar dataKey="count" fill="#8884d8" />
    </BarChart>
  );
};

export default TopIssuesChart;

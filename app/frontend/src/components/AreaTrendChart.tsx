import React from 'react';
import { AreaChart, Area, XAxis, YAxis, CartesianGrid, Tooltip, Legend } from 'recharts';
import { MonthData } from '../types/dashboardTypes';

interface AreaTrendChartProps {
  data: MonthData[];
}

const AreaTrendChart: React.FC<AreaTrendChartProps> = ({ data }) => {
  const areas = data[0].sentiments[0].areas.map(area => area.area);
  const chartData = data.map(month => {
    const result: any = { month: month.yearMonth };
    areas.forEach(area => {
      result[area] = month.sentiments[0].areas.find(a => a.area === area)?.count || 0;
    });
    return result;
  });

  const colors = ['#8884d8', '#82ca9d', '#ffc658', '#ff7300', '#0088FE', '#00C49F'];

  return (
    <AreaChart width={600} height={300} data={chartData}>
      <CartesianGrid strokeDasharray="3 3" />
      <XAxis dataKey="month" />
      <YAxis />
      <Tooltip />
      <Legend />
      {areas.map((area, index) => (
        <Area key={area} type="monotone" dataKey={area} stackId="1" stroke={colors[index % colors.length]} fill={colors[index % colors.length]} />
      ))}
    </AreaChart>
  );
};

export default AreaTrendChart;

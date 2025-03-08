import React, { useState } from 'react';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts';
import { MonthData } from '../types/dashboardTypes';

interface AreaTrendChartProps {
  data: MonthData[];
}

const AreaTrendChart: React.FC<AreaTrendChartProps> = ({ data }) => {
  const areas = Array.from(
    new Set(data.flatMap(month => month.sentiments.flatMap(sentiment => sentiment.areas.map(area => area.area))))
  );

  const [activeArea, setActiveArea] = useState<string | null>(null); // Track the currently active area or show all

  const chartData = data.map(month => {
    const result: any = { month: month.yearMonth };
    areas.forEach(areaName => {
      result[areaName] =
        month.sentiments.flatMap(s => s.areas).find(a => a.area === areaName)?.count || 0;
    });
    return result;
  });

  const handleLegendClick = (e: any) => {
    const clickedArea = e.dataKey as string;
    setActiveArea(prevActiveArea => (prevActiveArea === clickedArea ? null : clickedArea)); // Toggle between the clicked area and showing all
  };

  const colors = ['#8884d8', '#82ca9d', '#ffc658', '#ff7300', '#0088FE', '#00C49F', '#FF4D4F'];

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
        {areas.map((areaName, index) =>
          (activeArea === null || activeArea === areaName) && (
            <Line
              key={areaName}
              type="monotone"
              dataKey={areaName}
              stroke={colors[index % colors.length]}
              strokeWidth={2}
              dot={{ r: 4 }}
            />
          )
        )}
      </LineChart>
    </ResponsiveContainer>
  );
};

export default AreaTrendChart;

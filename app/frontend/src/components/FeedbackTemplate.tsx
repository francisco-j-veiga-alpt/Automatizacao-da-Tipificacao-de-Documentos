
import React, { useState, useEffect } from 'react';
import { FeedbackData } from '../types/feedbackTypes';
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
} from 'recharts';
import '../index.css';

interface FeedbackTemplateProps {
  title: string;
  timestamps?: string[];
  selectedTimestamp?: string;
  onTimestampChange?: (timestamp: string) => void;
  data: FeedbackData | null;
  loading: boolean;
  error: string | null;
}

const FeedbackTemplate: React.FC<FeedbackTemplateProps> = ({
  title,
  timestamps,
  selectedTimestamp,
  onTimestampChange,
  data,
  loading,
  error,
}) => {
  const [showLegend, setShowLegend] = useState(true);

  useEffect(() => {
    const handleResize = () => {
      setShowLegend(window.innerWidth > 768); // Hide legend on smaller screens
    };

    window.addEventListener('resize', handleResize);
    handleResize(); // Initial check

    return () => window.removeEventListener('resize', handleResize);
  }, []);

  if (loading) return <div>Loading...</div>;
  if (error) return <div>Error: {error}</div>;
  if (!data) return <div>No data available</div>;

  return (
    <div className="portal-container">
      <h1>
        {title} (
        {new Date(data.data).toLocaleDateString('pt-PT', {
          month: 'long',
          year: 'numeric',
        })}
        )
      </h1>

      {timestamps && selectedTimestamp && onTimestampChange && (
        <select
          className="custom-dropdown"
          value={selectedTimestamp}
          onChange={(e) => onTimestampChange(e.target.value)}
        >
          {timestamps.map((timestamp) => (
            <option key={timestamp} value={timestamp}>
              {timestamp}
            </option>
          ))}
        </select>
      )}

      {/* Recharts Bar Chart */}
      <div style={{ width: '100%', height: 300, marginTop: '20px' }}>
      <ResponsiveContainer>
        <BarChart data={data.analise}>
          <CartesianGrid strokeDasharray="3 3" />
          <XAxis
            dataKey="tema"
            tick={{ fontSize: 12, fill: '#666' }} // Custom font size and color
            angle={0} // Rotate labels for better readability
            textAnchor="end" // Align rotated labels
          />
          <YAxis unit="%" />
          <Tooltip />
          <Bar dataKey="percentagem" fill="#1FABEB" name="Percentagem" />
        </BarChart>
      </ResponsiveContainer>


      </div>

      {/* Table displaying complaint analysis */}
      <table className="portal-table">
        <thead>
          <tr>
            <th>Tema</th>
            <th>Descrição Detalhada</th>
            <th>Percentagem</th>
          </tr>
        </thead>
        <tbody>
          {data.analise.map((item, index) => (
            <tr key={index}>
              <td>{item.tema}</td>
              <td>{item.descricao}</td>
              <td>{item.percentagem}%</td>
            </tr>
          ))}
        </tbody>
      </table>

      {/* Suggestions and recommendations */}
      <div className="suggestions-container">
        <div className="suggestions-box">
          <h2>Sugestões dos Clientes</h2>
          <ul>
            {data.sugestoes_de_melhoria_dos_clientes.map((suggestion, index) => (
              <li key={index}>{suggestion}</li>
            ))}
          </ul>
        </div>

        <div className="suggestions-box">
          <h2>Recomendações de IA</h2>
          <ol>
            {data.propostas_de_melhoria_AI.map((proposal, index) => (
              <li key={index}>{proposal}</li>
            ))}
          </ol>
        </div>
      </div>
    </div>
  );
};

export default FeedbackTemplate;

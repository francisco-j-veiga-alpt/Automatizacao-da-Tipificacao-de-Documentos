
import React, { useState, useEffect } from 'react';
import { FeedbackData } from '../types/feedbackTypes';
import ProcessReport from '../components/ProcessReport';
import { fetchAvailableTimestamps, fetchReportData } from '../services/api';
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
  source: string; // Source for fetching data (e.g., "portal_da_queixa")
}

const FeedbackTemplate: React.FC<FeedbackTemplateProps> = ({ title, source }) => {
  const [feedbackData, setFeedbackData] = useState<FeedbackData | null>(null);
  const [timestamps, setTimestamps] = useState<string[]>([]);
  const [selectedTimestamp, setSelectedTimestamp] = useState<string>('');
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);

  // Load available timestamps
  useEffect(() => {
    const loadTimestamps = async () => {
      try {
        const data = await fetchAvailableTimestamps(`${source}_reports`);
        setTimestamps(data);
        if (data.length > 0) {
          setSelectedTimestamp(data[0]);
        }
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Unknown error');
      }
    };
    loadTimestamps();
  }, [source]);

  // Load report data when selectedTimestamp changes
  useEffect(() => {
    if (!selectedTimestamp) return;

    const [year, month] = selectedTimestamp.split('-');
    const loadReportData = async () => {
      setLoading(true);
      try {
        const data = await fetchReportData(source, year, month);
        setFeedbackData(data);
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Unknown error');
      } finally {
        setLoading(false);
      }
    };
    loadReportData();
  }, [selectedTimestamp, source]);

  if (loading) return <div>Loading...</div>;
  if (error) return <div>Error: {error}</div>;
  if (!feedbackData) return <div>No data available</div>;

  return (
    <>
      <ProcessReport source={source} />
      <div className="portal-container">
        <h1>
          {title} (
          {new Date(feedbackData.data).toLocaleDateString('pt-PT', {
            month: 'long',
            year: 'numeric',
          })}
          )
        </h1>

        {/* Dropdown for timestamps */}
        {timestamps.length > 0 && (
          <select
            className="custom-dropdown"
            value={selectedTimestamp}
            onChange={(e) => setSelectedTimestamp(e.target.value)}
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
            <BarChart data={feedbackData.analise}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis
                dataKey="tema"
                tick={{ fontSize: 12, fill: '#666' }}
                angle={0}
                textAnchor="end"
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
              <th>Total</th>
            </tr>
          </thead>
          <tbody>
            {feedbackData.analise.map((item, index) => (
              <tr key={index}>
                <td>{item.tema}</td>
                <td>{item.descricao}</td>
                <td>{item.percentagem}%</td>
                <td>{item.total}</td>
              </tr>
            ))}
          </tbody>
        </table>

        {/* Suggestions and recommendations */}
        <div className="suggestions-container">
          <div className="suggestions-box">
            <h2>Sugestões dos Clientes</h2>
            <ul>
              {feedbackData.sugestoes_de_melhoria_dos_clientes.map((suggestion, index) => (
                <li key={index}>{suggestion}</li>
              ))}
            </ul>
          </div>

          <div className="suggestions-box">
            <h2>Recomendações de IA</h2>
            <ol>
              {feedbackData.propostas_de_melhoria_AI.map((proposal, index) => (
                <li key={index}>{proposal}</li>
              ))}
            </ol>
          </div>
        </div>
      </div>
    </>
  );
};

export default FeedbackTemplate;

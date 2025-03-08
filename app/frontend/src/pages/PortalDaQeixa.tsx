// PortalDaQeixa.tsx
import React, { useEffect, useState } from 'react';
import { fetchAvailableTimestamps, fetchReportData } from '../services/api';
import '../index.css';

interface ComplaintAnalysis {
  tema: string;
  descricao: string;
  percentagem: number;
}

interface PortalData {
  analise: ComplaintAnalysis[];
  sugestoes_de_melhoria_dos_clientes: string[];
  propostas_de_melhoria_AI: string[];
  data: string;
}

const PortalDaQeixa: React.FC = () => {
  const [portalData, setPortalData] = useState<PortalData | null>(null);
  const [timestamps, setTimestamps] = useState<string[]>([]);
  const [selectedTimestamp, setSelectedTimestamp] = useState<string>('');
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);

  // Fetch available timestamps when the component mounts
  useEffect(() => {
    const loadTimestamps = async () => {
      try {
        const data = await fetchAvailableTimestamps();
        setTimestamps(data);
        if (data.length > 0) {
          setSelectedTimestamp(data[0]); // Default selection
        }
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Unknown error');
      }
    };

    loadTimestamps();
  }, []);

  // Fetch report data whenever the selected timestamp changes
  useEffect(() => {
    if (!selectedTimestamp) return;

    const [year, month] = selectedTimestamp.split('-');

    const loadReportData = async () => {
      setLoading(true);
      try {
        const data = await fetchReportData(year, month);
        setPortalData(data);
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Unknown error');
      } finally {
        setLoading(false);
      }
    };

    loadReportData();
  }, [selectedTimestamp]);

  if (loading) return <div>Loading...</div>;
  if (error) return <div>Error: {error}</div>;
  if (!portalData) return <div>No data available</div>;

  return (
    <div className="portal-container">
      <h1>Portal da Queixa - Análise de Reclamações ({new Date(portalData.data).toLocaleDateString('pt-PT', { month: 'long', year: 'numeric' })})</h1>

      {/* Dropdown for selecting a timestamp */}
      <select value={selectedTimestamp} onChange={(e) => setSelectedTimestamp(e.target.value)}>
        {timestamps.map((timestamp) => (
          <option key={timestamp} value={timestamp}>
            {timestamp}
          </option>
        ))}
      </select>

      {/* Table displaying complaint analysis */}
      <div className="portal-content">
        <table className="portal-table">
          <thead>
            <tr>
              <th>Tema</th>
              <th>Descrição Detalhada</th>
              <th>Percentagem</th>
            </tr>
          </thead>
          <tbody>
            {portalData.analise.map((item, index) => (
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
              {portalData.sugestoes_de_melhoria_dos_clientes.map((suggestion, index) => (
                <li key={index}>{suggestion}</li>
              ))}
            </ul>
          </div>
          <div className="suggestions-box">
            <h2>Recomendações de IA</h2>
            <ol>
              {portalData.propostas_de_melhoria_AI.map((proposal, index) => (
                <li key={index}>{proposal}</li>
              ))}
            </ol>
          </div>
        </div>
      </div>
    </div>
  );
};

export default PortalDaQeixa;

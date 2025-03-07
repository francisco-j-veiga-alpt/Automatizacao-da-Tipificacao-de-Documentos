// PortalDaQeixa.tsx
import React, { useEffect, useState } from 'react';
import { useParams } from 'react-router-dom';
import NavBar from '../components/NavBar';

import './PortalDaQeixa.css'; // Keep this for table and other specific styles
// Existing code and interfaces
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
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);
    const { year = '2025', month = '01' } = useParams();

    useEffect(() => {
        const fetchData = async () => {
            try {
                const response = await fetch(
                    `http://localhost:8000/feedback/portal_da_queixa/report?year=${year}&month=${month}`
                );

                if (!response.ok) {
                    throw new Error(`HTTP error! status: ${response.status}`);
                }

                const data: PortalData = await response.json();
                setPortalData(data);
            } catch (err) {
                setError(err instanceof Error ? err.message : 'Unknown error');
            } finally {
                setLoading(false);
            }
        };

        fetchData();
    }, [year, month]);

    if (loading) return <div className="dashboard">Loading...</div>;
    if (error) return <div className="dashboard">Error: {error}</div>;
    if (!portalData) return <div className="dashboard">No data available</div>;

    return (
        <div className="dashboard">
            <h1>Portal da Queixa - Análise de Reclamações ({new Date(portalData.data).toLocaleDateString('pt-PT', { month: 'long', year: 'numeric' })})</h1>

            <div className="chart">
                <h2>Distribuição de Reclamações</h2>
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
                            <tr key={item.tema}>
                                <td>{item.tema}</td>
                                <td>{item.descricao}</td>
                                <td>{item.percentagem}%</td>
                            </tr>
                        ))}
                    </tbody>
                </table>
            </div>

            <div className="chart-row">
                <div className="chart-half">
                    <h2>Sugestões dos Clientes</h2>
                    <ul>
                        {portalData.sugestoes_de_melhoria_dos_clientes.map((suggestion, index) => (
                            <li key={index} className="suggestion-item">
                                {suggestion}
                            </li>
                        ))}
                    </ul>
                </div>

                <div className="chart-half">
                    <h2>Recomendações de IA</h2>
                    <ol>
                        {portalData.propostas_de_melhoria_AI.map((proposal, index) => (
                            <li key={index} className="proposal-item">
                                {proposal}
                            </li>
                        ))}
                    </ol>
                </div>
            </div>
        </div>
    );
};

export default PortalDaQeixa;

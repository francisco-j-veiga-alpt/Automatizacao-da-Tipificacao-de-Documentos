// src/pages/PortalDaQeixa.tsx
import React, { useState, useEffect, useMemo } from 'react';
import { fetchSentimentSummary } from '../services/api';
import { SentimentSummaryResponse, TotalSentimentCounts } from '../types/summaryTypes';
import Loading from '../components/Loading';
import '../index.css'; // Ensure your global styles are imported
import {
  PieChart,
  Pie,
  Tooltip,
  Legend,
  ResponsiveContainer,
  Cell
} from 'recharts';

// --- SENTIMENT_COLORS constant remains the same ---
const SENTIMENT_COLORS: { [key: string]: string } = {
  'Very Negative': '#FF4D4F',
  'Negative': '#FFA500',
  'Neutral': '#8884d8',
  'None/Null': '#CCCCCC',
};

// --- Reusable SentimentChartSection component remains the same ---
interface SentimentChartSectionProps {
    title: string;
    queryDate: string | undefined;
    totalCount: number;
    chartData: { name: string; count: number }[];
    isLoading: boolean;
    error: string | null;
}

const SentimentChartSection: React.FC<SentimentChartSectionProps> = ({
    title, queryDate, totalCount, chartData, isLoading, error
}) => {
    // --- Custom label function remains the same ---
    const RADIAN = Math.PI / 180;
    const renderCustomizedLabel = ({ cx, cy, midAngle, innerRadius, outerRadius, percent }: any) => {
        const radius = innerRadius + (outerRadius - innerRadius) * 0.5;
        const x = cx + radius * Math.cos(-midAngle * RADIAN);
        const y = cy + radius * Math.sin(-midAngle * RADIAN);
        if ((percent * 100) < 5) return null;
        return ( <text x={x} y={y} fill="white" textAnchor={x > cx ? 'start' : 'end'} dominantBaseline="central" fontSize="12px"> {`${(percent * 100).toFixed(0)}%`} </text> );
    };

    // --- Component Rendering Logic remains the same ---
    if (isLoading) return <div className="dashboard-box" style={{ flex: 1 }}><Loading /></div>;
    if (error) return <div className="dashboard-box error-message" style={{ flex: 1 }}>Error: {error}</div>;
    if (totalCount === 0 && chartData.length === 0) {
        return ( <div className="dashboard-box" style={{ flex: 1 }}> <h2>{title}{queryDate ? ` for ${queryDate}` : ''}</h2> <p>No relevant sentiment counts found for this period.</p> </div> );
    }
    return (
        <div className="dashboard-box" style={{ flex: 1 }}>
          <h2>{title}{queryDate ? ` for ${queryDate}` : ''}</h2>
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', gap: '30px', height: '400px', width: '100%' }}>
            {/* Total Count Display */}
            <div style={{ textAlign: 'center', flexShrink: 0 }}><h4>Total Feedbacks</h4><p style={{ fontSize: '2em', fontWeight: 'bold', margin: 0 }}>{totalCount}</p></div>
            {/* Pie Chart Container */}
            <div style={{ flexGrow: 1, height: '100%', width: '70%' }}>
                {chartData.length > 0 ? (
                    <ResponsiveContainer width="100%" height="100%">
                      <PieChart>
                        <Pie data={chartData} labelLine={false} label={renderCustomizedLabel} outerRadius={120} fill="#8884d8" dataKey="count" nameKey="name">
                          {chartData.map((entry, index) => ( <Cell key={`cell-${index}`} fill={SENTIMENT_COLORS[entry.name] || '#8884d8'} /> ))}
                        </Pie>
                        <Tooltip />
                        <Legend />
                      </PieChart>
                    </ResponsiveContainer>
                ) : (<p style={{ textAlign: 'center', alignSelf: 'center' }}>(No sentiment counts gt 0 to display in chart)</p>)}
             </div>
          </div>
        </div>
    );
};
// --- End of Reusable Component ---


const PortalDaQeixa: React.FC = () => {
  // State for shared filters
  const currentYear = new Date().getFullYear();
  const currentMonth = new Date().getMonth() + 1;
  const [selectedYear, setSelectedYear] = useState<number>(currentYear);
  const [selectedMonth, setSelectedMonth] = useState<number>(currentMonth);

  // --- State for SEPARATE source filters ---
  const [filterSourceCF, setFilterSourceCF] = useState<string>(''); // For Customer Feedback
  const [filterSourceQF, setFilterSourceQF] = useState<string>(''); // For Qualtrics Feedback
  // ----------------------------------------

  // State for first dataset (Customer Feedback)
  const [summaryDataCF, setSummaryDataCF] = useState<SentimentSummaryResponse | null>(null);
  const [loadingCF, setLoadingCF] = useState<boolean>(false);
  const [errorCF, setErrorCF] = useState<string | null>(null);
  const collectionNameCF = "customer_feedback";

  // State for second dataset (Qualtrics Feedback)
  const [summaryDataQF, setSummaryDataQF] = useState<SentimentSummaryResponse | null>(null);
  const [loadingQF, setLoadingQF] = useState<boolean>(false);
  const [errorQF, setErrorQF] = useState<string | null>(null);
  const collectionNameQF = "qualtrics_feedback";

  // Fetch data for BOTH collections when shared filters OR individual source filters change
  useEffect(() => {
    const fetchData = async () => {
      setLoadingCF(true);
      setLoadingQF(true);
      setErrorCF(null);
      setErrorQF(null);

      const sourceToFilterCF = filterSourceCF.trim() || undefined;
      const sourceToFilterQF = filterSourceQF.trim() || undefined;

      // --- Construct filters for each call ---
      // Customer Feedback Filters
      const filtersCF: { [key: string]: any } = { needs_review: false };
      if (sourceToFilterCF) filtersCF['source'] = sourceToFilterCF;
      const filtersJsonCF = JSON.stringify(filtersCF);

      // Qualtrics Feedback Filters
      const filtersQF: { [key: string]: any } = { sentiment: { '$nin': [null, 'null'] } };
      if (sourceToFilterQF) filtersQF['source'] = sourceToFilterQF;
      const filtersJsonQF = JSON.stringify(filtersQF);
      // --------------------------------------

      // Use Promise.allSettled to fetch concurrently
      const results = await Promise.allSettled([
          // Call for Customer Feedback (using classification as group_by)
          fetchSentimentSummary(collectionNameCF, selectedYear, selectedMonth, null, "classification", "sentiment", "date", filtersJsonCF),
          // Call for Qualtrics Feedback (using crm_classification as group_by)
          fetchSentimentSummary(collectionNameQF, selectedYear, selectedMonth, null, "crm_classification", "sentiment", "date", filtersJsonQF) // <-- Changed group_by_column
      ]);

      // Process results for Customer Feedback
      if (results[0].status === 'fulfilled') {
          setSummaryDataCF(results[0].value);
      } else {
          setErrorCF(results[0].reason instanceof Error ? results[0].reason.message : 'Failed to fetch customer feedback summary.');
      }
      setLoadingCF(false);

       // Process results for Qualtrics Feedback
      if (results[1].status === 'fulfilled') {
          setSummaryDataQF(results[1].value);
      } else {
          setErrorQF(results[1].reason instanceof Error ? results[1].reason.message : 'Failed to fetch Qualtrics feedback summary.');
      }
      setLoadingQF(false);
    };

    fetchData();
    // --- Updated dependencies to include BOTH source filters ---
  }, [selectedYear, selectedMonth, filterSourceCF, filterSourceQF]);
  // ---------------------------------------------------------

  // --- Data transformation for Chart 1 (Customer Feedback) ---
  const chartDataCF = useMemo(() => { /* ... same as before ... */
    if (!summaryDataCF?.total_sentiment) return [];
    return Object.entries(summaryDataCF.total_sentiment).map(([name, count]) => ({ name, count })).filter(item => item.count > 0);
   }, [summaryDataCF]);
  const totalSentimentCountCF = useMemo(() => { /* ... same as before ... */
    if (!summaryDataCF?.total_sentiment) return 0;
    return Object.values(summaryDataCF.total_sentiment).reduce((sum, count) => sum + count, 0);
   }, [summaryDataCF]);

  // --- Data transformation for Chart 2 (Qualtrics Feedback) ---
   const chartDataQF = useMemo(() => { /* ... same as before ... */
    if (!summaryDataQF?.total_sentiment) return [];
    return Object.entries(summaryDataQF.total_sentiment).map(([name, count]) => ({ name: (name === 'null' || name === 'None') ? 'None/Null' : name, count })).filter(item => item.count > 0);
   }, [summaryDataQF]);
  const totalSentimentCountQF = useMemo(() => { /* ... same as before ... */
      if (!summaryDataQF?.total_sentiment) return 0;
      return Object.values(summaryDataQF.total_sentiment).reduce((sum, count) => sum + count, 0);
   }, [summaryDataQF]);


  // Year/Month options generation
  const yearOptions = Array.from({ length: 5 }, (_, i) => currentYear - i);
  const monthOptions = Array.from({ length: 12 }, (_, i) => i + 1);


  return (
    <div className="portal-container">
      <h1>Feedback Sentiment Summary</h1>

      {/* Filters Section */}
      <div className="filters" style={{ marginBottom: '20px', display: 'flex', flexWrap: 'wrap', gap: '15px', alignItems: 'flex-end' }}>
         {/* Date Filters (Shared) */}
         <div className="form-group">
           <label htmlFor="year-select">Year:</label>
            <select id="year-select" className="custom-dropdown" value={selectedYear} onChange={(e) => setSelectedYear(Number(e.target.value))}>
              {yearOptions.map(year => (<option key={year} value={year}>{year}</option>))}
            </select>
         </div>
         <div className="form-group">
           <label htmlFor="month-select">Month:</label>
            <select id="month-select" className="custom-dropdown" value={selectedMonth} onChange={(e) => setSelectedMonth(Number(e.target.value))}>
              {monthOptions.map(month => (<option key={month} value={month}>{new Date(selectedYear, month - 1).toLocaleString('default', { month: 'long' })} ({month})</option>))}
            </select>
         </div>

         {/* --- Source Filter for Customer Feedback --- */}
         <div className="form-group">
            <label htmlFor="source-filter-cf">Filter CF Source (Optional):</label>
            <input type="text" id="source-filter-cf" value={filterSourceCF} onChange={(e) => setFilterSourceCF(e.target.value)} placeholder="e.g., portal_da_queixa" style={{ padding: '8px', borderRadius: '4px', border: '1px solid #ccc' }}/>
            {filterSourceCF && (<button onClick={() => setFilterSourceCF('')} style={{ marginLeft: '5px', padding: '8px', cursor: 'pointer' }}>Clear</button>)}
         </div>
         {/* ----------------------------------------- */}

         {/* --- Source Filter for Qualtrics Feedback --- */}
         <div className="form-group">
            <label htmlFor="source-filter-qf">Filter QF Source (Optional):</label>
            <input type="text" id="source-filter-qf" value={filterSourceQF} onChange={(e) => setFilterSourceQF(e.target.value)} placeholder="e.g., web" style={{ padding: '8px', borderRadius: '4px', border: '1px solid #ccc' }}/>
            {filterSourceQF && (<button onClick={() => setFilterSourceQF('')} style={{ marginLeft: '5px', padding: '8px', cursor: 'pointer' }}>Clear</button>)}
         </div>
         {/* ------------------------------------------ */}

      </div>

      {/* Display Area with Side-by-Side Layout */}
      <div style={{ display: 'flex', gap: '20px', flexWrap: 'wrap', minHeight: '450px' }}>

        {/* Left Side: Customer Feedback */}
        <SentimentChartSection
            title="Customer Feedback"
            queryDate={summaryDataCF?.query_date || `${selectedYear}/${selectedMonth.toString().padStart(2, '0')}`}
            totalCount={totalSentimentCountCF}
            chartData={chartDataCF}
            isLoading={loadingCF}
            error={errorCF}
        />

        {/* Right Side: Qualtrics Feedback */}
         <SentimentChartSection
            // Updated Title
            title="Qualtrics Feedback (Null/None Sent.)"
            queryDate={summaryDataQF?.query_date || `${selectedYear}/${selectedMonth.toString().padStart(2, '0')}`}
            totalCount={totalSentimentCountQF}
            chartData={chartDataQF}
            isLoading={loadingQF}
            error={errorQF}
        />

      </div>

    </div>
  );
};

export default PortalDaQeixa;
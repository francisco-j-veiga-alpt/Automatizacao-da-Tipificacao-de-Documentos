// src/pages/PortalDaQeixa.tsx
import React, { useState, useEffect, useMemo } from 'react';
import { fetchSentimentSummary } from '../services/api';
import { SentimentSummaryResponse, TotalSentimentCounts, GroupingSummaryItem } from '../types/summaryTypes';
import Loading from '../components/Loading';
import '../index.css'; // Ensure your global styles are imported
import {
  PieChart, Pie, Tooltip as PieTooltip, Legend as PieLegend, ResponsiveContainer as PieResponsiveContainer, Cell, // Pie Chart imports
  BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip as BarTooltip, Legend as BarLegend, ResponsiveContainer as BarResponsiveContainer // Bar Chart imports
} from 'recharts';

// Define consistent colors for sentiments
const SENTIMENT_COLORS: { [key: string]: string } = {
  'Very Negative': '#FF4D4F',
  'Negative': '#FFA500',
  'Neutral': '#8884d8',
  'None/Null': '#CCCCCC',
};
// Define the sentiments we expect to stack/display in the bar chart
const SENTIMENT_KEYS = ['Very Negative', 'Negative', 'Neutral'];

// --- Reusable SentimentChartSection component (for Pie Charts - Corrected Definition) ---
interface SentimentChartSectionProps {
    title: string;
    queryDate: string | undefined;
    totalCount: number; // Type is number
    chartData: { name: string; count: number }[];
    isLoading: boolean;
    error: string | null;
}

// Use standard function definition to avoid potential React.FC type issues
function SentimentChartSection({
    title,
    queryDate,
    totalCount,
    chartData,
    isLoading,
    error
}: SentimentChartSectionProps) {

    const RADIAN = Math.PI / 180;
    const renderCustomizedLabel = ({ cx, cy, midAngle, innerRadius, outerRadius, percent }: any) => {
        const radius = innerRadius + (outerRadius - innerRadius) * 0.5;
        const x = cx + radius * Math.cos(-midAngle * RADIAN);
        const y = cy + radius * Math.sin(-midAngle * RADIAN);
        if ((percent * 100) < 5) return null;
        return ( <text x={x} y={y} fill="white" textAnchor={x > cx ? 'start' : 'end'} dominantBaseline="central" fontSize="12px"> {`${(percent * 100).toFixed(0)}%`} </text> );
    };

    if (isLoading) return <div className="dashboard-box" style={{ flex: 1 }}><Loading /></div>;
    if (error) return <div className="dashboard-box error-message" style={{ flex: 1 }}>Error: {error}</div>;
    if (totalCount === 0) {
        return ( <div className="dashboard-box" style={{ flex: 1 }}> <h2>{title}{queryDate ? ` for ${queryDate}` : ''}</h2> <p>No relevant sentiment counts found.</p> </div> );
    }
    return (
        <div className="dashboard-box" style={{ flex: 1 }}>
          <h2>{title}{queryDate ? ` for ${queryDate}` : ''}</h2>
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', gap: '30px', height: '400px', width: '100%' }}>
            <div style={{ textAlign: 'center', flexShrink: 0 }}><h4>Total Feedbacks</h4><p style={{ fontSize: '2em', fontWeight: 'bold', margin: 0 }}>{totalCount}</p></div>
            <div style={{ flexGrow: 1, height: '100%', width: '70%' }}>
                {chartData.length > 0 ? ( <PieResponsiveContainer width="100%" height="100%"><PieChart><Pie data={chartData} labelLine={false} label={renderCustomizedLabel} outerRadius={120} fill="#8884d8" dataKey="count" nameKey="name">{chartData.map((entry, index) => ( <Cell key={`cell-${index}`} fill={SENTIMENT_COLORS[entry.name] || '#8884d8'} /> ))}</Pie><PieTooltip /><PieLegend /></PieChart></PieResponsiveContainer> ) : (<p style={{ textAlign: 'center', alignSelf: 'center' }}>(No counts gt 0)</p>)}
             </div>
          </div>
        </div>
    );
};
// --- End of Reusable Component ---


const PortalDaQeixa: React.FC = () => {
  // --- State ---
  const currentYear = new Date().getFullYear();
  const currentMonth = new Date().getMonth() + 1;
  const [selectedYear, setSelectedYear] = useState<number>(currentYear);
  const [selectedMonth, setSelectedMonth] = useState<number>(currentMonth);
  const [filterSourceCF, setFilterSourceCF] = useState<string>('');
  const [filterSourceQF, setFilterSourceQF] = useState<string>('');
  const [currentGroupLevel, setCurrentGroupLevel] = useState<number | null>(1);
  const [summaryDataCF, setSummaryDataCF] = useState<SentimentSummaryResponse | null>(null);
  const [loadingCF, setLoadingCF] = useState<boolean>(false);
  const [errorCF, setErrorCF] = useState<string | null>(null);
  const collectionNameCF = "customer_feedback";
  const [summaryDataQF, setSummaryDataQF] = useState<SentimentSummaryResponse | null>(null);
  const [loadingQF, setLoadingQF] = useState<boolean>(false);
  const [errorQF, setErrorQF] = useState<string | null>(null);
  const collectionNameQF = "qualtrics_feedback";
  // -------------

  // --- useEffect for Data Fetching ---
  useEffect(() => {
    const fetchData = async () => {
      setLoadingCF(true); setLoadingQF(true);
      setErrorCF(null); setErrorQF(null);

      const sourceToFilterCF = filterSourceCF.trim() || undefined;
      const sourceToFilterQF = filterSourceQF.trim() || undefined;

      const filtersCF: { [key: string]: any } = { needs_review: false };
      if (sourceToFilterCF) filtersCF['source'] = sourceToFilterCF;
      const filtersJsonCF = JSON.stringify(filtersCF);

      const filtersQF: { [key: string]: any } = { sentiment: { '$nin': [null, 'null'] } };
      if (sourceToFilterQF) filtersQF['source'] = sourceToFilterQF;
      const filtersJsonQF = JSON.stringify(filtersQF);

      console.log("Fetching CF with filters:", filtersJsonCF, "Level:", currentGroupLevel);
      console.log("Fetching QF with filters:", filtersJsonQF, "Level:", currentGroupLevel);

      const results = await Promise.allSettled([
          fetchSentimentSummary(collectionNameCF, selectedYear, selectedMonth, currentGroupLevel, "classification", "sentiment", "date", filtersJsonCF),
          fetchSentimentSummary(collectionNameQF, selectedYear, selectedMonth, currentGroupLevel, "crm_classification", "sentiment", "date", filtersJsonQF)
      ]);

      if (results[0].status === 'fulfilled') setSummaryDataCF(results[0].value);
      else setErrorCF(results[0].reason instanceof Error ? results[0].reason.message : 'Failed.');
      setLoadingCF(false);

      if (results[1].status === 'fulfilled') setSummaryDataQF(results[1].value);
      else setErrorQF(results[1].reason instanceof Error ? results[1].reason.message : 'Failed.');
      setLoadingQF(false);
    };
    fetchData();
  }, [selectedYear, selectedMonth, filterSourceCF, filterSourceQF, currentGroupLevel]);
  // ---------------------------------

  // --- useMemo for Pie Chart 1 Data ---
  const chartDataCF = useMemo(() => {
    if (!summaryDataCF?.total_sentiment) return [];
    return Object.entries(summaryDataCF.total_sentiment).map(([name, count]) => ({ name, count })).filter(item => item.count > 0);
   }, [summaryDataCF]);
  const totalSentimentCountCF = useMemo(() => {
    if (!summaryDataCF?.total_sentiment) return 0;
    return Object.values(summaryDataCF.total_sentiment).reduce((sum, count) => sum + count, 0);
   }, [summaryDataCF]);
  // ----------------------------------

  // --- useMemo for Pie Chart 2 Data ---
   const chartDataQF = useMemo(() => {
    if (!summaryDataQF?.total_sentiment) return [];
    return Object.entries(summaryDataQF.total_sentiment).map(([name, count]) => ({ name: (name === 'null' || name === 'None') ? 'None/Null' : name, count })).filter(item => item.count > 0);
   }, [summaryDataQF]);
  const totalSentimentCountQF = useMemo(() => {
      if (!summaryDataQF?.total_sentiment) return 0;
      return Object.values(summaryDataQF.total_sentiment).reduce((sum, count) => sum + count, 0);
   }, [summaryDataQF]);
  // ----------------------------------

  // --- useMemo for Bar Chart Data ---
  const mergedChartData = useMemo(() => {
    const cfMap = new Map<string, GroupingSummaryItem>();
    summaryDataCF?.grouping_summary.forEach(item => cfMap.set(item.grouping_value, item));
    const qfMap = new Map<string, GroupingSummaryItem>();
    summaryDataQF?.grouping_summary.forEach(item => qfMap.set(item.grouping_value, item));

    const allKeys = new Set([ ...Array.from(cfMap.keys()), ...Array.from(qfMap.keys()) ]); // Fixed iteration

    const merged = Array.from(allKeys).map(key => {
        const cfItem = cfMap.get(key);
        const qfItem = qfMap.get(key);
        const dataPoint: any = { name: key, cf_total: cfItem?.group_total_count || 0, qf_total: qfItem?.group_total_count || 0 };
        SENTIMENT_KEYS.forEach(sentimentKey => {
             dataPoint[`cf_${sentimentKey}`] = cfItem?.sentiment_counts_total[sentimentKey] || 0;
             dataPoint[`qf_${sentimentKey}`] = qfItem?.sentiment_counts_total[sentimentKey] || 0;
        });
        return dataPoint;
    });
    merged.sort((a, b) => a.name.localeCompare(b.name));
    // console.log("Merged Chart Data:", merged); // Keep for debugging if needed
    return merged;
  }, [summaryDataCF, summaryDataQF]);
  // ---------------------------------

  // Year/Month options generation
  const yearOptions = Array.from({ length: 5 }, (_, i) => currentYear - i);
  const monthOptions = Array.from({ length: 12 }, (_, i) => i + 1);


  return (
    <div className="portal-container">
      <h1>Feedback Sentiment Summary</h1>

      {/* Filters Section */}
      <div className="filters" style={{ marginBottom: '20px', display: 'flex', flexWrap: 'wrap', gap: '15px', alignItems: 'flex-end' }}>
         {/* Date Filters */}
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
         {/* CF Source Filter */}
         <div className="form-group">
            <label htmlFor="source-filter-cf">Filter CF Source (Optional):</label>
            <input type="text" id="source-filter-cf" value={filterSourceCF} onChange={(e) => setFilterSourceCF(e.target.value)} placeholder="e.g., portal_da_queixa" style={{ padding: '8px', borderRadius: '4px', border: '1px solid #ccc' }}/>
            {filterSourceCF && (<button onClick={() => setFilterSourceCF('')} style={{ marginLeft: '5px', padding: '8px', cursor: 'pointer' }}>Clear</button>)}
         </div>
         {/* QF Source Filter */}
         <div className="form-group">
            <label htmlFor="source-filter-qf">Filter QF Source (Optional):</label>
            <input type="text" id="source-filter-qf" value={filterSourceQF} onChange={(e) => setFilterSourceQF(e.target.value)} placeholder="e.g., web" style={{ padding: '8px', borderRadius: '4px', border: '1px solid #ccc' }}/>
            {filterSourceQF && (<button onClick={() => setFilterSourceQF('')} style={{ marginLeft: '5px', padding: '8px', cursor: 'pointer' }}>Clear</button>)}
         </div>
          {/* Group Level Selector */}
         <div className="form-group">
            <label htmlFor="group-level-select">Group Level (0=Full):</label>
            <input type="number" id="group-level-select" value={currentGroupLevel === null ? 0 : currentGroupLevel} onChange={(e) => { const level = parseInt(e.target.value, 10); setCurrentGroupLevel(level <= 0 ? null : level); }} min="0" style={{ padding: '8px', borderRadius: '4px', border: '1px solid #ccc', width: '60px' }}/>
         </div>
      </div>

      {/* --- Display Area --- */}

      {/* Row 1: Side-by-Side Pie Charts */}
      <div style={{ display: 'flex', gap: '20px', flexWrap: 'wrap', marginBottom: '30px', minHeight: '450px' }}>
        <SentimentChartSection
            title="Customer Feedback"
            queryDate={summaryDataCF?.query_date || `${selectedYear}/${selectedMonth.toString().padStart(2, '0')}`}
            totalCount={totalSentimentCountCF}
            chartData={chartDataCF}
            isLoading={loadingCF}
            error={errorCF}
        />
         <SentimentChartSection
            title="Qualtrics Feedback"
            queryDate={summaryDataQF?.query_date || `${selectedYear}/${selectedMonth.toString().padStart(2, '0')}`}
            totalCount={totalSentimentCountQF}
            chartData={chartDataQF}
            isLoading={loadingQF}
            error={errorQF}
        />
      </div>

      {/* Row 2: Comparative Bar Chart (HORIZONTAL LAYOUT) */}
       {(loadingCF || loadingQF) && !errorCF && !errorQF && <Loading />}
       {(errorCF || errorQF) && ( <div className="error-message"> Bar Chart Data Error: CF: {errorCF || 'OK'} | QF: {errorQF || 'OK'} </div> )}

       {!loadingCF && !loadingQF && !errorCF && !errorQF && mergedChartData.length > 0 && (
        <div className="dashboard-box full-width">
           <h2>Comparison by Classification (Level: {currentGroupLevel ?? 'Full Path'})</h2>
           {/* Use dynamic height based on number of bars */}
           <BarResponsiveContainer width="100%" height={Math.max(600, mergedChartData.length * 40)}>
              {/* === Horizontal BarChart Configuration === */}
              <BarChart
                 data={mergedChartData}
                 layout="vertical" // Set layout to vertical
                 margin={{ top: 20, right: 50, left: 200, bottom: 20 }} // Adjusted margins
                >
                <CartesianGrid strokeDasharray="3 3" />
                {/* X Axis (Count) */}
                <XAxis type="number" allowDecimals={false} />
                {/* Y Axis (Category/Classification) */}
                <YAxis
                    type="category"
                    dataKey="name"
                    width={180} // Adjusted width for labels
                    tick={{ fontSize: 10 }}
                    interval={0}
                    />
                <BarTooltip />
                <BarLegend verticalAlign="top" wrapperStyle={{ paddingBottom: '20px' }}/>

                {/* CF Bars (Horizontal) */}
                {SENTIMENT_KEYS.map(sentiment => (
                     <Bar key={`cf-${sentiment}`} dataKey={`cf_${sentiment}`} stackId="cf" fill={SENTIMENT_COLORS[sentiment] || '#8884d8'} name={`CF ${sentiment}`} />
                ))}
                 {/* QF Bars (Horizontal) */}
                 {SENTIMENT_KEYS.map(sentiment => (
                     <Bar key={`qf-${sentiment}`} dataKey={`qf_${sentiment}`} stackId="qf" fill={SENTIMENT_COLORS[sentiment] || '#82ca9d'} name={`QF ${sentiment}`} />
                 ))}
              </BarChart>
              {/* ======================================= */}
            </BarResponsiveContainer>
        </div>
      )}
       {/* Message if no merged data */}
       {!loadingCF && !loadingQF && !errorCF && !errorQF && mergedChartData.length === 0 && (
           <div className="dashboard-box full-width" style={{minHeight: '100px', display:'flex', alignItems:'center', justifyContent:'center'}}>No matching classification data found for comparison at this level.</div>
       )}
      {/* ----------------------------- */}

    </div> // End portal-container
  );
};

export default PortalDaQeixa;
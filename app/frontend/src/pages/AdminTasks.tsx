// src/pages/AdminTasks.tsx
import React, { useState, useEffect, useMemo } from 'react';
// Assuming api.ts is in ../services/ and types are in ../types/
import { processSourceFeedback, fetchLatestTimestamp, fetchReviewSummary } from '../services/api';
import { ProcessPortalDaQueixaParams, ReviewSummaryResponse, FeedbackDocument, NeedsReviewCounts, FeedbackReportData } from '../types/adminTypes'; // Ensure all needed types are imported
import Loading from '../components/Loading';
import '../index.css';
// Import necessary Recharts components
import {
  PieChart, Pie, Tooltip, Legend, ResponsiveContainer, Cell
} from 'recharts';

// Define colors for Review Status Pie Chart
const REVIEW_STATUS_COLORS: { [key: string]: string } = {
  'Needs Review': '#FF4D4F', // Red
  'No Review Needed': '#28a745', // Green
};


const AdminTasks: React.FC = () => {
    // --- State for Processing Form ---
    const defaultFormData: ProcessPortalDaQueixaParams = {
        to_date: new Date().toISOString().split('T')[0],
        last_date: '',
        begin_pages_to_look: 1,
        num_of_pages_to_look: 5,
        delete_feedback: true,
    };
    const [formData, setFormData] = useState<ProcessPortalDaQueixaParams>(defaultFormData);
    const [latestTimestamp, setLatestTimestamp] = useState<string | null>(null);
    const [loadingProcess, setLoadingProcess] = useState<boolean>(false);
    const [loadingTimestamp, setLoadingTimestamp] = useState<boolean>(true);
    const [successMessage, setSuccessMessage] = useState<string | null>(null);
    const [errorMessage, setErrorMessage] = useState<string | null>(null);
    // --------------------------------

    // --- State for Review Summary ---
    const [reviewSummary, setReviewSummary] = useState<ReviewSummaryResponse | null>(null);
    const [loadingSummary, setLoadingSummary] = useState<boolean>(true);
    const [errorSummary, setErrorSummary] = useState<string | null>(null);
    const [selectedReview, setSelectedReview] = useState<FeedbackDocument | null>(null);
    // ------------------------------

    // Define sources
    const processingSource = "portal_da_queixa";
    const summarySource = "customer_feedback"; // Source to get counts/reviews from

    // --- useEffect for Initial Data Fetching (Timestamp & Summary) ---
    useEffect(() => {
        let isMounted = true;
        setLoadingTimestamp(true);
        setLoadingSummary(true);
        setErrorSummary(null); // Clear previous error

        const loadInitialData = async () => {
            // Using Promise.allSettled for concurrent fetching
            const results = await Promise.allSettled([
                fetchLatestTimestamp(summarySource),
                fetchReviewSummary(summarySource)
            ]);

            // Process Timestamp Result
            if (results[0].status === 'fulfilled') {
                const timestamp = results[0].value;
                if (isMounted) {
                    const datePart = timestamp ? timestamp.split(' ')[0] : '';
                    setLatestTimestamp(datePart || 'Never processed');
                    if (datePart) {
                        setFormData(prev => ({ ...prev, last_date: datePart }));
                    }
                }
            } else {
                console.error('Error fetching latest timestamp:', results[0].reason);
                if (isMounted) setLatestTimestamp('Error fetching timestamp');
            }
             if (isMounted) setLoadingTimestamp(false);

            // Process Review Summary Result
            if (results[1].status === 'fulfilled') {
                 if (isMounted) {
                    setReviewSummary(results[1].value);
                 }
            } else {
                 console.error('Error fetching review summary:', results[1].reason);
                 if (isMounted) {
                     setErrorSummary(results[1].reason instanceof Error ? results[1].reason.message : "Failed to load review summary.");
                     setReviewSummary(null);
                 }
            }
            if (isMounted) setLoadingSummary(false);
        };

        loadInitialData();

        // Cleanup function
        return () => { isMounted = false; };
    }, [summarySource]); // Run only on mount or if summarySource changes
    // -----------------------------------------------------------------

    // Handle input changes for the form fields
    const handleInputChange = (e: React.ChangeEvent<HTMLInputElement>) => {
        const { name, value, type, checked } = e.target;
        setFormData(prev => ({
            ...prev,
            [name]: type === 'checkbox' ? checked : (type === 'number' ? parseInt(value, 10) || 0 : value),
        }));
    };

    // Handle form submission to trigger processing
     const handleSubmit = async (e: React.FormEvent<HTMLFormElement>) => {
        e.preventDefault();
        setLoadingProcess(true);
        setSuccessMessage(null); setErrorMessage(null);
        setErrorSummary(null); // Clear summary error on new process attempt

        // Validation...
        if (!formData.to_date || !formData.last_date || new Date(formData.to_date) <= new Date(formData.last_date) || formData.num_of_pages_to_look < 1) {
             setErrorMessage('Please check form inputs (Dates valid? Pages >= 1?).');
             setLoadingProcess(false); return;
        }

        try {
            console.log(`Submitting params for ${processingSource}:`, formData);
            const response = await processSourceFeedback(processingSource, formData);
            setSuccessMessage(`Processing successful! Backend response: ${JSON.stringify(response)}`);

            // --- Re-fetch Timestamp AND Summary ---
            setLoadingTimestamp(true); setLoadingSummary(true); // Set loading for refetches
            setErrorSummary(null); // Clear previous summary error

            fetchLatestTimestamp(summarySource)
                .then(ts => setLatestTimestamp(ts ? ts.split(' ')[0] : 'Never processed'))
                .catch(console.error)
                .finally(() => setLoadingTimestamp(false));

            fetchReviewSummary(summarySource)
                .then(summary => setReviewSummary(summary))
                .catch(err => setErrorSummary(err instanceof Error ? err.message : "Failed to reload summary."))
                .finally(() => setLoadingSummary(false));
            // ------------------------------------

        } catch (error: any) {
            console.error("Processing Error:", error);
            setErrorMessage(`Error: ${error.message || 'An unexpected error occurred.'}`);
        } finally {
            setLoadingProcess(false);
        }
    };
    // --- End handleSubmit ---


    // --- useMemo for Review Count Chart Data ---
    const reviewCountChartData = useMemo(() => {
        if (!reviewSummary?.counts) return [];
        return [
            { name: 'Needs Review', value: reviewSummary.counts.needs_review_true ?? 0 },
            { name: 'No Review Needed', value: reviewSummary.counts.needs_review_false ?? 0 },
        ].filter(item => item.value > 0); // Only include slices with value > 0
    }, [reviewSummary]);
    // ---------------------------------------

    // --- useMemo for Total Review Count ---
    const totalReviewCount = useMemo(() => {
        if (!reviewSummary?.counts) return 0;
        return (reviewSummary.counts.needs_review_true ?? 0) + (reviewSummary.counts.needs_review_false ?? 0);
    }, [reviewSummary]);
    // ------------------------------------

    // --- Custom label function for Review Count Pie Chart ---
    const RADIAN = Math.PI / 180;
    const renderReviewCountLabel = ({ cx, cy, midAngle, innerRadius, outerRadius, percent, index, name, value }: any) => {
        // Position label in the middle of the slice thickness
        const radius = innerRadius + (outerRadius - innerRadius) * 0.5;
        const x = cx + radius * Math.cos(-midAngle * RADIAN);
        const y = cy + radius * Math.sin(-midAngle * RADIAN);

        // Don't render label if percentage is too small (e.g., less than 5%)
        // Adjust or remove this threshold if needed
        if (!percent || percent < 0.05) return null;

        // Make sure value exists before rendering (optional check, but safe)
        if (value === undefined || value === null) return null;

        return (
        <text
            x={x}
            y={y}
            fill="white" // Assuming slice colors provide enough contrast
            textAnchor={x > cx ? 'start' : 'end'}
            dominantBaseline="central"
            fontSize="12px" // You might be able to increase this slightly now
            fontWeight="bold"
        >
            {/* --- MODIFIED: Display only percentage --- */}
            {`${(percent * 100).toFixed(0)}%`}
            {/* ---------------------------------------- */}
        </text>
        );
    };
    // ------------------------------------------------------


    // --- JSX Rendering ---
    return (
        <div className="portal-container">
            <h1>Admin Tasks</h1>

             {/* Processing Form Section */}
            <div className="dashboard-box" style={{ marginBottom: '30px' }}>
                 <h2>Process Portal da Queixa Feedback</h2>
                 <p>
                    Trigger the backend process to scrape feedback from '{processingSource}', analyze it, and store it in the `{summarySource}` collection.
                    <br/><em>(Last processed date shown below is from the `{summarySource}` collection).</em>
                </p>
                 <form onSubmit={handleSubmit} className="process-feedback-form" style={{width: 'auto', maxWidth: '500px'}}>
                     {/* Form Inputs */}
                     <div className="form-group"> <label>Last Processed Date:</label> <input type="text" value={loadingTimestamp ? 'Loading...' : latestTimestamp ?? 'N/A'} readOnly disabled style={{ backgroundColor: '#eee' }}/> </div>
                     <div className="form-group"> <label htmlFor="last_date">Process From Date (Exclusive):</label> <input type="date" id="last_date" name="last_date" value={formData.last_date} onChange={handleInputChange} required style={{ padding: '8px', borderRadius: '4px', border: '1px solid #ccc', width: '95%' }}/> </div>
                     <div className="form-group"> <label htmlFor="to_date">Process Until Date (Inclusive):</label> <input type="date" id="to_date" name="to_date" value={formData.to_date} onChange={handleInputChange} required style={{ padding: '8px', borderRadius: '4px', border: '1px solid #ccc', width: '95%' }}/> </div>
                     <div className="form-group"> <label htmlFor="begin_pages_to_look">Start Page Number (Portal da Queixa):</label> <input type="number" id="begin_pages_to_look" name="begin_pages_to_look" value={formData.begin_pages_to_look} onChange={handleInputChange} min="1" required style={{ padding: '8px', borderRadius: '4px', border: '1px solid #ccc', width: '95%' }}/> </div>
                     <div className="form-group"> <label htmlFor="num_of_pages_to_look">Number of Pages to Check (Portal da Queixa):</label> <input type="number" id="num_of_pages_to_look" name="num_of_pages_to_look" value={formData.num_of_pages_to_look} onChange={handleInputChange} min="1" required style={{ padding: '8px', borderRadius: '4px', border: '1px solid #ccc', width: '95%' }}/> </div>
                     <div className="form-group checkbox-group"> <label htmlFor="delete_feedback"> <input type="checkbox" id="delete_feedback" name="delete_feedback" checked={formData.delete_feedback} onChange={handleInputChange} /> {' '} Delete Existing Feedback in Date Range First (in `{summarySource}`) </label> </div>
                     <button type="submit" className="toggle-form-button" disabled={loadingProcess || loadingTimestamp}> {loadingProcess ? 'Processing...' : 'Start Processing'} </button>
                     {/* Messages */}
                     {successMessage && <div className="message success-message" style={{marginTop: '15px'}}>{successMessage}</div>}
                     {errorMessage && <div className="message error-message" style={{marginTop: '15px'}}>{errorMessage}</div>}
                 </form>
            </div>


            {/* Review Summary Section */}
            <div className="dashboard-box full-width">
                <h2>Review Summary ({summarySource})</h2>
                {loadingSummary && <Loading />}
                {errorSummary && <div className="error-message">Error loading summary: {errorSummary}</div>}
                {reviewSummary && !loadingSummary && !errorSummary && (
                    <div>
                        {/* Count Visualization Area (Enlarged) */}
                        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', gap: '40px', marginBottom: '20px', paddingBottom: '20px', borderBottom: '1px solid #eee', flexWrap: 'wrap' }}>
                             {/* Total Count Display */}
                             <div style={{ textAlign: 'center', flexShrink: 0 }}>
                                 <h4>Total Items Checked</h4>
                                 <p style={{ fontSize: '2.5em', fontWeight: 'bold', margin: 0, color: '#333' }}>
                                     {totalReviewCount}
                                 </p>
                             </div>
                             {/* Pie Chart for Counts (Enlarged Container & Pie) */}
                             <div style={{ width: '450px', height: '280px' }}> {/* Increased Size */}
                                {reviewCountChartData.length > 0 ? (
                                    <ResponsiveContainer width="100%" height="100%">
                                        <PieChart>
                                            <Pie
                                                data={reviewCountChartData}
                                                cx="50%" cy="50%"
                                                outerRadius={110} // Increased Radius
                                                fill="#8884d8"
                                                dataKey="value"
                                                nameKey="name"
                                                labelLine={false}
                                                label={renderReviewCountLabel}
                                            >
                                                {reviewCountChartData.map((entry, index) => (
                                                    <Cell key={`cell-review-${index}`} fill={REVIEW_STATUS_COLORS[entry.name] || '#8884d8'} />
                                                ))}
                                            </Pie>
                                            <Tooltip />
                                            <Legend layout="vertical" align="right" verticalAlign="middle"/>
                                        </PieChart>
                                    </ResponsiveContainer>
                                ) : ( <p style={{ textAlign: 'center', alignSelf: 'center' }}>(Counts are zero)</p> )}
                            </div>
                        </div>
                        {/* End Count Visualization */}


                        {/* Display Lists and Selected Item */}
                        <div style={{ display: 'flex', gap: '20px', flexWrap: 'wrap' }}>
                            {/* Column for Needs Review List */}
                            <div style={{ flex: 1, minWidth: '300px' }}>
                                <h3>Needs Review ({reviewSummary.counts.needs_review_true ?? 0} items / Last 10 shown)</h3>
                                <div style={{ maxHeight: '400px', overflowY: 'auto', border: '1px solid #ccc', borderRadius: '4px', padding: '5px' }}>
                                    {reviewSummary.recent_needs_review.length > 0 ? ( reviewSummary.recent_needs_review.map((item: FeedbackDocument, index: number) => (<div key={`nr-${index}-${item.date || index}`} onClick={() => setSelectedReview(item)} style={{ padding: '8px', borderBottom: '1px dashed #eee', cursor: 'pointer', backgroundColor: selectedReview === item ? '#e0f7fa' : 'transparent', whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis' }} title={item.feedback_full_text}> {new Date(item.date).toLocaleDateString()} - {item.user_id?.substring(0, 20)}... - {item.feedback_full_text.substring(0, 30)}... </div>)) ) : (<p>None found</p>)}
                                </div>
                            </div>

                            {/* Column for Doesn't Need Review List */}
                             <div style={{ flex: 1, minWidth: '300px' }}>
                                <h3>Doesn't Need Review ({reviewSummary.counts.needs_review_false ?? 0} items / Last 10 shown)</h3>
                                 <div style={{ maxHeight: '400px', overflowY: 'auto', border: '1px solid #ccc', borderRadius: '4px', padding: '5px' }}>
                                    {reviewSummary.recent_does_not_need_review.length > 0 ? ( reviewSummary.recent_does_not_need_review.map((item: FeedbackDocument, index: number) => (<div key={`dnr-${index}-${item.date || index}`} onClick={() => setSelectedReview(item)} style={{ padding: '8px', borderBottom: '1px dashed #eee', cursor: 'pointer', backgroundColor: selectedReview === item ? '#e0f7fa' : 'transparent', whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis' }} title={item.feedback_full_text}> {new Date(item.date).toLocaleDateString()} - {item.user_id?.substring(0, 20)}... - {item.feedback_full_text.substring(0, 30)}... </div>)) ) : (<p>None found</p>)}
                                </div>
                            </div>

                             {/* Column for Selected Review Details */}
                             <div style={{ flex: 2, minWidth: '300px', border: '1px solid #eee', borderRadius: '4px', padding: '15px', backgroundColor: '#f9f9f9' }}>
                                <h3>Selected Review Details</h3>
                                {selectedReview ? ( <div> <p><strong>Date:</strong> {selectedReview.date ? new Date(selectedReview.date).toLocaleString() : 'N/A'}</p> <p><strong>User ID:</strong> {selectedReview.user_id ?? 'N/A'}</p> <p><strong>Source:</strong> {selectedReview.source ?? 'N/A'}</p> <p><strong>Sentiment:</strong> {selectedReview.sentiment ?? 'N/A'}</p> <p><strong>Classification:</strong> {selectedReview.classification ?? 'N/A'}</p> <p><strong>Needs Review:</strong> {selectedReview.needs_review ? 'Yes' : 'No'}</p> <p><strong>Summary:</strong> {selectedReview.feedback_summary ?? 'N/A'}</p> <hr style={{margin: '10px 0'}}/> <p><strong>Full Text:</strong></p> <p style={{ whiteSpace: 'pre-wrap', maxHeight: '250px', overflowY: 'auto', border: '1px solid #ddd', padding: '10px', backgroundColor: 'white', fontSize: '0.9em', lineHeight: '1.4' }}> {selectedReview.feedback_full_text ?? 'N/A'} </p> </div> ) : ( <p>Click on a review from the lists to see details.</p> )}
                             </div>
                        </div>
                    </div>
                )}
                 {/* Message if no summary data loaded */}
                {!reviewSummary && !loadingSummary && !errorSummary && ( <p>No review summary data available.</p> )}
            </div>
            {/* --- End Review Summary Section --- */}

        </div> // End portal-container
    );
};

export default AdminTasks;
// src/pages/AdminTasks.tsx
import React, { useState, useEffect } from 'react';
// Assuming api.ts is in ../services/
import { processSourceFeedback, fetchLatestTimestamp } from '../services/api'; // Updated import name
// Assuming adminTypes.ts is in ../types/
import { ProcessPortalDaQueixaParams } from '../types/adminTypes'; // Type name might need update if it becomes generic later
import Loading from '../components/Loading'; // Assuming Loading component exists
import '../index.css'; // Import common styles

const AdminTasks: React.FC = () => {
    // Define default form state
    const defaultFormData: ProcessPortalDaQueixaParams = {
        to_date: new Date().toISOString().split('T')[0], // Default to today
        last_date: '', // Will be fetched
        begin_pages_to_look: 1,
        num_of_pages_to_look: 5, // Default reasonable number
        delete_feedback: true, // Default to delete (safer for reprocessing)
    };

    const [formData, setFormData] = useState<ProcessPortalDaQueixaParams>(defaultFormData);
    const [latestTimestamp, setLatestTimestamp] = useState<string | null>(null);
    const [loading, setLoading] = useState<boolean>(false);
    const [loadingTimestamp, setLoadingTimestamp] = useState<boolean>(true);
    const [successMessage, setSuccessMessage] = useState<string | null>(null);
    const [errorMessage, setErrorMessage] = useState<string | null>(null);

    // This source variable defines the target for PROCESSING
    const source = "portal_da_queixa";
    // This source variable defines the target for checking the LAST PROCESSED DATE
    const timestampSource = "customer_feedback"; // Corrected source for timestamp

    // Fetch the latest timestamp on component mount
    useEffect(() => {
        setLoadingTimestamp(true);
        // Use the corrected source for fetching timestamp
        fetchLatestTimestamp(timestampSource)
            .then(timestamp => {
                const datePart = timestamp ? timestamp.split(' ')[0] : ''; // Extract date part
                setLatestTimestamp(datePart || 'Never processed');
                // Pre-fill last_date only if a valid date was found
                if (datePart) {
                    setFormData(prev => ({ ...prev, last_date: datePart }));
                }
            })
            .catch(error => {
                console.error('Error fetching latest timestamp:', error);
                setLatestTimestamp('Error fetching timestamp');
            })
            .finally(() => {
                 setLoadingTimestamp(false);
            });
        // Run only on mount, timestampSource is constant here
    }, []);

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
        e.preventDefault(); // Prevent default form submission
        setLoading(true);
        setSuccessMessage(null);
        setErrorMessage(null);

        // Basic Frontend Validation
        if (!formData.to_date || !formData.last_date) {
            setErrorMessage('Please select valid "To Date" and "Last Date".');
            setLoading(false);
            return;
        }
        if (new Date(formData.to_date) <= new Date(formData.last_date)) {
             setErrorMessage('"To Date" must be after "Last Date".');
             setLoading(false);
             return;
        }
        if (formData.num_of_pages_to_look < 1) {
             setErrorMessage('"Number of Pages" must be at least 1.');
             setLoading(false);
             return;
        }
        // End Basic Validation

        try {
            // Optional: Add confirmation dialog, especially for delete_feedback=true
            // if (formData.delete_feedback && !window.confirm("Are you sure you want to delete existing feedback in the date range before processing?")) {
            //     setLoading(false);
            //     return;
            // }

            console.log(`Submitting params for ${source}:`, formData);
            // Call API function with the PROCESSING source ("portal_da_queixa")
            const response = await processSourceFeedback(source, formData);
            setSuccessMessage(`Processing successful! Backend response: ${JSON.stringify(response)}`);
            // Re-fetch timestamp from the correct collection after successful processing
            fetchLatestTimestamp(timestampSource)
                .then(ts => setLatestTimestamp(ts ? ts.split(' ')[0] : 'Never processed'))
                .catch(console.error);

        } catch (error: any) {
            console.error("Processing Error:", error);
            setErrorMessage(`Error: ${error.message || 'An unexpected error occurred.'}`);
        } finally {
            setLoading(false);
        }
    };

    // --- JSX Rendering ---
    return (
        <div className="portal-container"> {/* Use existing class */}
            <h1>Admin Tasks</h1>

            <div className="dashboard-box"> {/* Use existing class */}
                {/* Title clarifies this section */}
                <h2>Process Portal da Queixa Feedback</h2>
                <p>
                    Trigger the backend process to scrape new feedback from Portal da Queixa, analyze it using AI, and store it in the database (for source: `{source}`). {/* <<< CORRECTED: Used defined 'source' variable */}
                    <br/><em>(Last processed date shown below is from the `{timestampSource}` collection).</em>
                </p>

                <form onSubmit={handleSubmit} className="process-feedback-form" style={{width: 'auto', maxWidth: '500px'}}> {/* Adjust styles */}
                    <div className="form-group">
                        <label>Last Processed Date:</label>
                        <input type="text" value={loadingTimestamp ? 'Loading...' : latestTimestamp ?? 'N/A'} readOnly disabled style={{ backgroundColor: '#eee' }}/>
                    </div>

                    <div className="form-group">
                        <label htmlFor="last_date">Process From Date (Exclusive):</label>
                        <input
                            type="date"
                            id="last_date"
                            name="last_date"
                            value={formData.last_date}
                            onChange={handleInputChange}
                            required
                            style={{ padding: '8px', borderRadius: '4px', border: '1px solid #ccc', width: '95%' }}
                        />
                    </div>

                    <div className="form-group">
                        <label htmlFor="to_date">Process Until Date (Exclusive):</label>
                        <input
                            type="date"
                            id="to_date"
                            name="to_date"
                            value={formData.to_date}
                            onChange={handleInputChange}
                            required
                            style={{ padding: '8px', borderRadius: '4px', border: '1px solid #ccc', width: '95%' }}
                        />
                    </div>

                     <div className="form-group">
                        <label htmlFor="begin_pages_to_look">Start Page Number (Portal da Queixa):</label>
                        <input
                            type="number"
                            id="begin_pages_to_look"
                            name="begin_pages_to_look"
                            value={formData.begin_pages_to_look}
                            onChange={handleInputChange}
                            min="1"
                            required
                            style={{ padding: '8px', borderRadius: '4px', border: '1px solid #ccc', width: '95%' }}
                        />
                    </div>

                     <div className="form-group">
                        <label htmlFor="num_of_pages_to_look">Number of Pages to Check (Portal da Queixa):</label>
                        <input
                            type="number"
                            id="num_of_pages_to_look"
                            name="num_of_pages_to_look"
                            value={formData.num_of_pages_to_look}
                            onChange={handleInputChange}
                            min="1"
                            required
                            style={{ padding: '8px', borderRadius: '4px', border: '1px solid #ccc', width: '95%' }}
                        />
                    </div>

                     <div className="form-group checkbox-group">
                        <label htmlFor="delete_feedback">
                            <input
                                type="checkbox"
                                id="delete_feedback"
                                name="delete_feedback"
                                checked={formData.delete_feedback}
                                onChange={handleInputChange}
                            />
                           {' '} Delete Existing Feedback in Date Range First (in target collection)
                        </label>
                    </div>

                    <button type="submit" className="toggle-form-button" disabled={loading || loadingTimestamp}>
                        {loading ? 'Processing...' : 'Start Processing'}
                    </button>

                    {/* Message display */}
                    {successMessage && <div className="message success-message" style={{marginTop: '15px'}}>{successMessage}</div>}
                    {errorMessage && <div className="message error-message" style={{marginTop: '15px'}}>{errorMessage}</div>}

                </form>
            </div>
        </div>
    );
};

export default AdminTasks;
import React, { useState } from 'react';
import { processReport, ProcessReportParams } from '../services/api';
import '../index.css';

interface ProcessReportProps {
  source: string; // Source passed as a prop
}

const ProcessReport: React.FC<ProcessReportProps> = ({ source }) => {
  const [formData, setFormData] = useState<ProcessReportParams>({
    year: new Date().getFullYear(),
    month: new Date().getMonth() + 1,
    delete_report: true,
  });

  const [loading, setLoading] = useState(false);
  const [successMessage, setSuccessMessage] = useState<string | null>(null);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const [showForm, setShowForm] = useState(false); // State to toggle form visibility

  const handleInputChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const { name, value, checked, type } = e.target;
    setFormData({
      ...formData,
      [name]: type === 'checkbox' ? checked : value,
    });
  };

  const handleSubmit = async () => {
    setLoading(true);
    setSuccessMessage(null);
    setErrorMessage(null);

    try {
      const response = await processReport(formData, source);
      setSuccessMessage('Success! Report processed successfully.');
    } catch (error: any) {
      const message =
        error.response?.data?.detail || error.message || 'An unexpected error occurred.';
      setErrorMessage(`Error: ${message}`);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="process-report-container">
      <button
        className="toggle-form-button"
        onClick={() => setShowForm(!showForm)}
      >
        {showForm ? 'Hide Form' : 'Process Report'}
      </button>

      {showForm && (
        <div className="process-report-form">
          <h3>Process Report</h3>
          <div className="form-group">
            <label>Year:</label>
            <input
              type="number"
              name="year"
              value={formData.year}
              onChange={handleInputChange}
              min="2000"
              max={new Date().getFullYear()}
            />
          </div>
          <div className="form-group">
            <label>Month:</label>
            <input
              type="number"
              name="month"
              value={formData.month}
              onChange={handleInputChange}
              min="1"
              max="12"
            />
          </div>
          <div className="form-group checkbox-group">
            <label>
              <input
                type="checkbox"
                name="delete_report"
                checked={formData.delete_report}
                onChange={handleInputChange}
              />
              Delete Existing Report
            </label>
          </div>
          <button
            className="process-report-button"
            onClick={handleSubmit}
            disabled={loading}
          >
            {loading ? 'Processing...' : 'Submit'}
          </button>

          {successMessage && <div className="success-message">{successMessage}</div>}
          {errorMessage && <div className="error-message">{errorMessage}</div>}
        </div>
      )}
    </div>
  );
};

export default ProcessReport;

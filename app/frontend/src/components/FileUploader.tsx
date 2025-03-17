// src/components/FileUploader.tsx
import React, { useState } from 'react';
import { uploadFileToApi } from '../services/api'; // Import the correct API function
import '../index.css'; // Import global styles for consistency

interface FileUploaderProps {
  source: string; // Source for the upload (e.g., "portal_da_queixa" or "qualtrics_chatbot")
  onUploadComplete?: () => void; // Optional callback for when upload completes
}

const FileUploader: React.FC<FileUploaderProps> = ({ source, onUploadComplete }) => {
  const [file, setFile] = useState<File | null>(null);
  const [year, setYear] = useState<number | ''>(''); // State for year input
  const [month, setMonth] = useState<number | ''>(''); // State for month input
  const [deleteReport, setDeleteReport] = useState<boolean>(true); // State for delete_report checkbox
  const [message, setMessage] = useState<string>('');
  const [loading, setLoading] = useState<boolean>(false);
  const [showForm, setShowForm] = useState<boolean>(false); // Toggle state for showing/hiding the form

  const handleFileChange = (event: React.ChangeEvent<HTMLInputElement>) => {
    if (event.target.files) {
      setFile(event.target.files[0]);
    }
  };

  const handleSubmit = async (event: React.FormEvent) => {
    event.preventDefault();
    if (!file) {
      setMessage('Please select a file.');
      return;
    }
    if (!year || !month) {
      setMessage('Please provide both year and month.');
      return;
    }

    setLoading(true);
    try {
      await uploadFileToApi(file, source, year, month, deleteReport); // Pass file, source, year, month, and deleteReport to the API
      setMessage('File uploaded successfully!');
      if (onUploadComplete) onUploadComplete();
    } catch (error) {
      console.error(error);
      setMessage('Failed to upload file.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="process-feedback-container">
      {/* Toggle Button */}
      <button
        className="toggle-form-button"
        onClick={() => setShowForm((prev) => !prev)}
      >
        {showForm ? 'Hide Upload Form' : 'Show Upload Form'}
      </button>

      {/* Conditionally Render Form */}
      {showForm && (
        <form onSubmit={handleSubmit} className="process-feedback-form">
          <h3>Upload File</h3>
          <div className="form-group">
            <label htmlFor="file">Select File:</label>
            <input type="file" id="file" accept=".xls" onChange={handleFileChange} />
          </div>
          <div className="form-group">
            <label htmlFor="year">Year:</label>
            <input
              type="number"
              id="year"
              value={year}
              onChange={(e) => setYear(Number(e.target.value))}
              placeholder="Enter year (e.g., 2025)"
            />
          </div>
          <div className="form-group">
            <label htmlFor="month">Month:</label>
            <input
              type="number"
              id="month"
              value={month}
              onChange={(e) => setMonth(Number(e.target.value))}
              placeholder="Enter month (1-12)"
            />
          </div>
          <div className="form-group checkbox-group">
            <label>
              <input
                type="checkbox"
                checked={deleteReport}
                onChange={(e) => setDeleteReport(e.target.checked)}
              />
              Delete Existing Data?
            </label>
          </div>
          <button type="submit" className="submit-button">
            {loading ? 'Uploading...' : 'Upload'}
          </button>
          {message && (
            <p
              className={`message ${
                message.includes('successfully') ? 'success-message' : 'error-message'
              }`}
            >
              {message}
            </p>
          )}
        </form>
      )}
    </div>
  );
};

export default FileUploader;

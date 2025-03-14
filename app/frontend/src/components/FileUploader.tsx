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

    setLoading(true);
    try {
      await uploadFileToApi(file, source); // Pass both file and source to the API
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
            <input type="file" id="file" accept=".csv" onChange={handleFileChange} />
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

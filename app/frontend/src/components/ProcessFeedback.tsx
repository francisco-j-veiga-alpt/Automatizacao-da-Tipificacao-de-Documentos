import React, { useState } from 'react';
import { processFeedback, ProcessFeedbackParams } from '../services/api';

const ProcessFeedback: React.FC = () => {
  const [formData, setFormData] = useState<ProcessFeedbackParams>({
    to_date: '',
    last_date: '',
    begin_pages_to_look: 1,
    num_of_pages_to_look: 5,
    delete_feedback: true,
  });

  const [loading, setLoading] = useState(false);
  const [successMessage, setSuccessMessage] = useState<string | null>(null);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const [showForm, setShowForm] = useState(false); // State to toggle form visibility

  const handleInputChange = (e: React.ChangeEvent<HTMLInputElement | HTMLSelectElement>) => {
    const target = e.target;
    if (target instanceof HTMLInputElement) {
      const { name, value, checked, type } = target;
      setFormData({
        ...formData,
        [name]: type === 'checkbox' ? checked : value,
      });
    } else if (target instanceof HTMLSelectElement) {
      const { name, value } = target;
      setFormData({
        ...formData,
        [name]: value,
      });
    }
  };

  const handleSubmit = async () => {
    setLoading(true);
    setSuccessMessage(null);
    setErrorMessage(null);

    try {
      // Validate dates
      if (!formData.to_date || !formData.last_date) {
        throw new Error('Both "To Date" and "Last Date" must be valid dates.');
      }

      const response = await processFeedback(formData);

      setSuccessMessage(`Success! Number of inserted IDs: ${response.num_inserted_ids}`);
    } catch (error: any) {
      const message =
        error.response?.data?.detail || error.message || 'An unexpected error occurred.';
      setErrorMessage(`Error: ${message}`);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="process-feedback-container">
      <button
        className="toggle-form-button"
        onClick={() => setShowForm(!showForm)}
      >
        {showForm ? 'Hide Form' : 'Process Feedback'}
      </button>

      {showForm && (
        <div className="process-feedback-form">
          <h3>Process Feedback</h3>
          <div className="form-group">
            <label>To Date:</label>
            <input
              type="date"
              name="to_date"
              value={formData.to_date}
              onChange={handleInputChange}
              placeholder="yyyy/mm/dd" // Placeholder for European format
            />
          </div>
          <div className="form-group">
            <label>Last Date:</label>
            <input
              type="date"
              name="last_date"
              value={formData.last_date}
              onChange={handleInputChange}
              placeholder="yyyy/mm/dd" // Placeholder for European format
            />
          </div>
          <div className="form-group">
            <label>Begin Pages to Look:</label>
            <input
              type="number"
              name="begin_pages_to_look"
              value={formData.begin_pages_to_look}
              onChange={handleInputChange}
              min="1"
            />
          </div>
          <div className="form-group">
            <label>Number of Pages to Look:</label>
            <input
              type="number"
              name="num_of_pages_to_look"
              value={formData.num_of_pages_to_look}
              onChange={handleInputChange}
              min="2"
            />
          </div>
          <div className="form-group checkbox-group">
            <label>
              <input
                type="checkbox"
                name="delete_feedback"
                checked={formData.delete_feedback}
                onChange={handleInputChange}
              />
              Delete Feedback
            </label>
          </div>
          <button
            className="process-feedback-button"
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

export default ProcessFeedback;

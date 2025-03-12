import axios from 'axios';

// Fetch dashboard data for the last N months
export const fetchDashboardData = async (numLastMonths: number) => {
  try {
    const response = await axios.get(`http://localhost:8000/feedback/portal-da-queixa/summary?num_last_months=${numLastMonths}`);
    return response.data[0]; // Adjust based on your API's response structure
  } catch (error) {
    console.error('Error fetching dashboard data:', error);
    throw error;
  }
};

// Fetch available timestamps
export const fetchAvailableTimestamps = async (source: string) => {
  try {
    const response = await axios.get(`http://localhost:8000/feedback/${source}/list-timestamp`);
    return response.data;
  } catch (error) {
    console.error('Error fetching timestamps:', error);
    throw error;
  }
};

// Fetch report data for a specific year and month
export const fetchReportData = async (source:string, year: string, month: string) => {
  try {
    const response = await axios.get(`http://localhost:8000/feedback/${source}/report?year=${year}&month=${month}`);
    return response.data;
  } catch (error) {
    console.error('Error fetching report:', error);
    throw error;
  }
};

export interface ProcessFeedbackParams {
  to_date?: string;
  last_date?: string;
  begin_pages_to_look: number;
  num_of_pages_to_look: number;
  delete_feedback: boolean;
}

export const processFeedback = async (params: ProcessFeedbackParams) => {
  try {
    const response = await axios.post('http://localhost:8000/feedback/portal-da-queixa/process', params);
    return response.data; // Should return { num_inserted_ids: number }
  } catch (error) {
    console.error('Error processing feedback:', error);
    throw error;
  }
};

export interface ProcessReportParams {
  year: number;
  month: number;
  delete_report: boolean;
}

export const processReport = async (params: ProcessReportParams, source: string) => {
  try {
    const response = await axios.post(
      `http://localhost:8000/feedback/${source}/process-report`,
      {
        year: params.year,
        month: params.month,
        delete_report: params.delete_report,
      }
    );
    return response.data; // Should return { inserted_id: "ok" }
  } catch (error) {
    console.error('Error processing report:', error);
    throw error;
  }
};

export const fetchLatestTimestamp = async (source: string): Promise<string> => {
  try {
    const response = await axios.get(`http://localhost:8000/feedback/${source}/latest-timestamp`);
    return response.data; // The API returns a string like "2025-02-22 00:00:00"
  } catch (error) {
    console.error('Error fetching latest timestamp:', error);
    throw error;
  }
};

export const uploadFileToApi = async (file: File): Promise<void> => {
  const formData = new FormData();
  formData.append('file', file);

  try {
    await axios.post(`http://localhost:8000/feedback/cliente-misterio/upload`, formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
    });
  } catch (error) {
    console.error('Failed to upload file:', error);
    throw error;
  }
};
import axios from 'axios';
import { SentimentSummaryResponse } from '../types/summaryTypes';

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

export const uploadFileToApi = async (
  file: File,
  source: string,
  year: number,
  month: number,
  deleteReport: boolean
): Promise<void> => {
  const formData = new FormData();
  formData.append('file', file);
  formData.append('year', String(year)); // Add year to form data
  formData.append('month', String(month)); // Add month to form data
  formData.append('delete_report', String(deleteReport)); // Add delete_report to form data

  try {
    await axios.post(`http://localhost:8000/feedback/${source}/upload`, formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
    });
  } catch (error) {
    console.error('Failed to upload file:', error);
    throw error;
  }
};



export const fetchSentimentSummary = async (
  collectionName: string,
  year: number,
  month: number,
  groupLevel?: number | null,
  groupByColumn?: string,
  sentimentColumn?: string,
  dateField?: string,
  filtersJson?: string | null // Accepts the pre-formatted JSON string for filters
): Promise<SentimentSummaryResponse> => {

  // Construct query parameters dynamically
  const params = new URLSearchParams({
    year: String(year),
    month: String(month),
  });
  if (groupLevel !== undefined && groupLevel !== null) {
    params.append('group_level', String(groupLevel));
  }
  // Pass the filters_json string directly if provided
  if (filtersJson) {
      params.append('filters_json', filtersJson);
  }
   if (groupByColumn) {
    params.append('group_by_column', groupByColumn);
  }
  if (sentimentColumn) {
    params.append('sentiment_column', sentimentColumn);
  }
   if (dateField) {
    params.append('date_field', dateField);
  }

  // Log the request being sent
  console.log(`API Request: GET /feedback/summary/${collectionName}`, params.toString());

  try {
    const response = await axios.get(
      // Ensure your backend API base URL is correct (e.g., http://localhost:8000)
      `http://localhost:8000/feedback/summary/${collectionName}`, // Using relative path assumes proxy or same origin
      { params }
    );
    // Log the raw response data
    console.log(`Raw Response Data for ${collectionName}:`, response.data);
    return response.data;
  } catch (error) {
    console.error(`Error fetching sentiment summary for ${collectionName}:`, error);
    if (axios.isAxiosError(error) && error.response) {
       // Log detailed error response if available
       console.error("API Error Response:", error.response.data);
       throw new Error(`API Error (${error.response.status}): ${error.response.data?.detail || error.message}`);
    } else if (error instanceof Error) {
       throw new Error(`Failed to fetch sentiment summary: ${error.message}`);
    } else {
       throw new Error('Failed to fetch sentiment summary due to an unknown error');
    }
  }
};
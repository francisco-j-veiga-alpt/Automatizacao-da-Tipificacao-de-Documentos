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
export const fetchAvailableTimestamps = async () => {
  try {
    const response = await axios.get(`http://localhost:8000/feedback/portal_da_queixa_reports/list-timestamp`);
    return response.data;
  } catch (error) {
    console.error('Error fetching timestamps:', error);
    throw error;
  }
};

// Fetch report data for a specific year and month
export const fetchReportData = async (year: string, month: string) => {
  try {
    const response = await axios.get(`http://localhost:8000/feedback/portal_da_queixa/report?year=${year}&month=${month}`);
    return response.data;
  } catch (error) {
    console.error('Error fetching report:', error);
    throw error;
  }
};

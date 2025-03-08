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

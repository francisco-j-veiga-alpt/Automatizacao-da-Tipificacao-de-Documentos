import axios from 'axios';

const API_URL = 'http://localhost:8000/feedback/portal-da-queixa/summary';

export const fetchDashboardData = async (numLastMonths: number) => {
  try {
    const response = await axios.get(`${API_URL}?num_last_months=${numLastMonths}`);
    return response.data[0];
  } catch (error) {
    console.error('Error fetching dashboard data:', error);
    throw error;
  }
};

// services/api.ts
export const fetchPortalDaQueixaData = async (year: number, month: number) => {
  const response = await fetch(
    `/api/feedback/portal_da_queixa/report?year=${year}&month=${month}`
  );
  return response.json();
};


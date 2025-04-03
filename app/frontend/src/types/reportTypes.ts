// src/types/reportTypes.ts

export interface EmergingTopic {
  // Assuming English keys based on the model definition
  topic: string;
  justification: string;
}

export interface FeedbackReportData {
  // Assuming English keys based on the model definition
  customer_suggestions: string[];
  ai_improvement_proposals: string[];
  emerging_topics: EmergingTopic[];
  date: string; // ISO date string
  source_qualtrics?: string; // Example specific field from output
  // Add other fields if the report contains them (e.g., source, year, month)
  source?: string;
  year?: number;
  month?: number;
}
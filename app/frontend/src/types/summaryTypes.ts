// src/types/summaryTypes.ts

// Represents the structure of the total_sentiment object
export interface TotalSentimentCounts {
    // Keys will be sentiment names (e.g., 'Negative', 'Neutral', 'null')
    [sentiment: string]: number;
  }
  
  // Represents one item in the grouping_summary list
  export interface GroupingSummaryItem {
    grouping_value: string;
    group_total_count: number;
    sentiment_counts_total: {
      [sentiment: string]: number;
    };
  }
  
  // Represents the overall structure of the API response
  export interface SentimentSummaryResponse {
    query_date: string;
    total_sentiment: TotalSentimentCounts;
    grouping_summary: GroupingSummaryItem[];
  }
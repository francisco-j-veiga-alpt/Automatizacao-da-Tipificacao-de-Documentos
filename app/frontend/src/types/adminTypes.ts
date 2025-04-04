// src/types/adminTypes.ts

export interface EmergingTopic { // Ensure export
  topic: string;
  justification: string;
}

export interface FeedbackReportData { // Ensure export
  customer_suggestions: string[];
  ai_improvement_proposals: string[];
  emerging_topics: EmergingTopic[];
  date: string;
  source_qualtrics?: string;
  source?: string;
  year?: number;
  month?: number;
}

export interface FeedbackDocument {
  date: string; // ISO String from jsonable_encoder
  user_id: string;
  feedback_full_text: string;
  source: string;
  feedback_summary?: string;
  classification?: string;
  sentiment?: string;
  needs_review: boolean;
  // Add any other fields you want to display
}

// Counts returned by the API
export interface NeedsReviewCounts {
   needs_review_true: number;
   needs_review_false: number;
}

// Full response structure from the review summary API endpoint
export interface ReviewSummaryResponse {
    counts: NeedsReviewCounts;
    recent_needs_review: FeedbackDocument[];
    recent_does_not_need_review: FeedbackDocument[];
}
// Interface matching the expected input for the backend
// Assuming InputPostPortalDaQuiexa is similar to InputProcessPortalDaQueixa
// based on frontend component code pasted previously (ProcessFeedback.tsx)
export interface ProcessPortalDaQueixaParams {
    to_date: string; // Use string to match date input value
    last_date: string; // Use string to match date input value
    begin_pages_to_look: number;
    num_of_pages_to_look: number;
    delete_feedback: boolean;
  }
  
  // Interface for the expected success response
  export interface ProcessPortalDaQueixaResponse {
    num_inserted_ids: number;
  }
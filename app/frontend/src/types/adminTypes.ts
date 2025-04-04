// src/types/adminTypes.ts

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
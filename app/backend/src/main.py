import json
import os
from fastapi import FastAPI, APIRouter, HTTPException, Query, status
from fastapi.middleware.cors import CORSMiddleware
from typing import Dict, Optional, Union
from src.llm_utils.models import feedback_classifier_generic, process_feedback_generic
from src.conn_utils.mongo_conn import connect_to_collection, insert_data, delete_data_between_dates, InputProcessBase,\
    InputProcessPortalDaQueixa, get_classifications_as_string, retrieve_grouped_sentiment_counts
from src.utils.utils_portal_da_queixa import get_portal_da_queixa_feedback

db_host = os.environ.get("MONGO_HOST")
db_user = os.environ.get("MONGO_PRINCIPAL_USER")
db_password = os.environ.get("MONGO_PRINCIPAL_PASSWORD")
db_feedback = os.environ.get("MONGO_DB_CUSTOMER_FEEDBACK")
portal_da_queixa = os.environ.get("PORTAL_DA_QUEIXA")
db_collection_portal_da_queixa = os.environ.get("MONGO_COLLECTION_PORTAL_DA_QUEIXA")
db_collection_portal_da_queixa_reports = os.environ.get("MONGO_COLLECTION_PORTAL_DA_QUEIXA_REPORTS")
db_collection_qualtrics_chatbot = os.environ.get("MONGO_COLLECTION_QUALTRICS_CHATBOT")
db_collection_qualtrics_chatbot_reports = os.environ.get("MONGO_COLLECTION_QUALTRICS_CHATBOT_REPORTS")
db_collection_cliente_misterio = os.environ.get("MONGO_COLLECTION_CLIENTE_MISTERIO")
db_collection_cliente_misterio_reports = os.environ.get("MONGO_COLLECTION_CLIENTE_MISTERIO_REPORTS")
db_collection_classifications = os.environ.get("MONGO_COLLECTION_CLASSIFICATIONS")
db_collection_customers_feedback = os.environ.get("MONGO_COLLECTION_CUSTOMER_FEEDBACK")

uri_feedback = f"mongodb://{db_user}:{db_password}@{db_host}/{db_feedback}"

app = FastAPI()

# Configure CORS (keep this as it is)
origins = [
    "http://localhost:3000",
    "http://localhost:8000",
    "http://127.0.0.1:3000"
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# --- App API ---
@app.get("/")
async def root():
    return {"message": "API is UP!"}


# --- Feedback API ---
feedback_router = APIRouter(prefix="/feedback", tags=["customer feedback"])

@feedback_router.get("/")
async def feedback_state():
    return {"message": "Feedback API is UP!"}


@feedback_router.post("/process/{source}", status_code=status.HTTP_201_CREATED)
async def process_sources(params: Union[InputProcessBase, InputProcessPortalDaQueixa], source: str):
    try:
        db, collection, client = connect_to_collection(uri_feedback, db_feedback, db_collection_customers_feedback)

        # Fetch data based on source type
        if source == portal_da_queixa and isinstance(params, InputProcessPortalDaQueixa):
            res = get_portal_da_queixa_feedback(params)
            if len(res.list) == 0:
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="No Data from Portal da Queixa")
        else:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Source not available!")
        
        # Delete existing feedback if requested
        if params.delete_feedback:
            delete_data_between_dates(collection, params.last_date, params.to_date, "data")

        class_collection = db[db_collection_classifications]
        
        classifications = get_classifications_as_string(class_collection)

        # Process feedback with LLM
        chain = feedback_classifier_generic()
        output = process_feedback_generic(chain, res, classifications, 10)

        # Insert processed data into MongoDB
        insert_result = insert_data(collection, output.model_dump()["list"])
        
        return {"num_inserted_ids": len(insert_result)}
    
    except Exception as e:
        e.add_note(f"Error process sources: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))
    finally:
        if client:
            client.close()


@feedback_router.get("/summary/{collection_name}")
async def get_summary_data(
    # Path parameter
    collection_name: str,
    # Query parameters for date range
    year: int,
    month: int = Query(..., ge=1, le=12), # Month is required
    # Query parameters matching retrieve_grouped_sentiment_counts function args
    group_by_column: str = Query("classification", description="Field to group results by."),
    sentiment_column: str = Query("sentiment", description="Field containing sentiment values."),
    group_level: Optional[int] = Query(None, description="Hierarchy level (1-based) to group by. Uses full path if None.", ge=1),
    date_field: str = Query("date", description="Field containing date information."),
    # --- New parameter for filters ---
    filters_json: Optional[str] = Query(None, description="Optional: JSON string representing key-value pairs for filtering (e.g., '{\"source\":\"portal_da_queixa\"}')")
    # ---------------------------------
):
    """
    Retrieves summarized sentiment data for a specific collection, year, and month,
    allowing configuration of grouping fields, hierarchy level, and additional filters
    via query parameters.
    """
    client = None # Initialize client to None
    filter_by_columns_dict: Optional[Dict] = None # Initialize filter dict

    try:
        # --- Parse filters_json ---
        if filters_json:
            try:
                filter_by_columns_dict = json.loads(filters_json)
                if not isinstance(filter_by_columns_dict, dict):
                    raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="filters_json must be a valid JSON object (dictionary).")
            except json.JSONDecodeError:
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid JSON format in filters_json parameter.")
        # -------------------------

        if not collection_name or not collection_name.strip():
             raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Collection name cannot be empty.")

        # Connect to the specific collection
        try:
            db, collection, client = connect_to_collection(
                uri_feedback, db_feedback, collection_name, create_collection=False
            )
        except ValueError as e:
             raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Collection '{collection_name}' not found in database '{db_feedback}'. Details: {e}")


        # Call the aggregation function passing all configurable parameters
        summary_result = retrieve_grouped_sentiment_counts(
            collection=collection,
            year=year,
            month=month,
            group_by_column=group_by_column,
            sentiment_column=sentiment_column,
            group_level=group_level,
            filter_by_columns=filter_by_columns_dict, # Pass the parsed dictionary
            date_field=date_field
        )

        if summary_result is None:
             raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to retrieve summary data due to an internal error.")

        # Return the result (potentially empty if no data matches)
        return summary_result

    except HTTPException as http_exc:
         raise http_exc
    except Exception as e:
        print(f"Error in get_summary_data: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"An unexpected error occurred: {type(e).__name__}")
    finally:
        if client:
            client.close()





# Include the routers in the main app
app.include_router(feedback_router)

#find . -type d -name __pycache__ -exec rm -r {} \+

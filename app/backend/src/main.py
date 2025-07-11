import calendar
import json
import os
from fastapi import FastAPI, APIRouter, File, Form, HTTPException, Path, Query, UploadFile, status
from fastapi.encoders import jsonable_encoder
from fastapi.middleware.cors import CORSMiddleware
from typing import Dict, Optional, Union, Any

from dateutil.relativedelta import relativedelta
from src.utils.utils import qualtrics_provdoria
from src.llm_utils.models import feedback_classifier_generic, feedback_report, feedback_sentiment_analyzer, process_feedback_generic, process_feedback_sentiment, process_report
from src.conn_utils.mongo_conn import FeedbackQuestionnaire, ListFeedbackQuestionnaire, ListFeedbackQuestionnaireSentiment, connect_to_collection, get_data_by_year_month, get_max_timestamp, get_review_summary, insert_data, delete_data_between_dates, InputProcessBase,\
    InputProcessPortalDaQueixa, get_classifications_as_string, retrieve_grouped_sentiment_counts, InputReport
from src.utils.utils_portal_da_queixa import get_portal_da_queixa_feedback
from datetime import date, datetime, time, timedelta

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
            delete_data_between_dates(collection, params.last_date, params.to_date, "date")

        class_collection = db[db_collection_classifications]
        
        classifications = get_classifications_as_string(class_collection)

        # Process feedback with LLM
        chain = feedback_classifier_generic()
        output = process_feedback_generic(chain, res, classifications, 1)

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


@feedback_router.post("/process-report/{source_feed}/{source_dept}/{report_dest}", status_code=status.HTTP_201_CREATED)
async def process_report_api(
    request_data: InputReport,
    source_feed: str = Path(..., title="Feedbacks collection in mongodb"),
    source_dept: str = Path(..., title="Feedbacks collection in mongodb"),
    report_dest: str = Path(..., title="Feedbacks collection in mongodb")
    ):

    print(source_feed, source_dept, report_dest)

    try:
        today = date.today()
        if request_data.year > today.year:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid Year!")
        elif request_data.year == today.year and request_data.month > today.month:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid Month!")
        elif request_data.month < 1 or request_data.month > 12:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid Month!")

        db, collection, client = connect_to_collection(uri_feedback, db_feedback, source_feed)
        feed_month = get_data_by_year_month(collection=collection, date_field="date", month=request_data.month, year=request_data.year, project={}, filter_dict={"sentiment": {"$nin": [None, "null"]}, "source_qualtrics": source_dept})
        feed_month = ["Feedback: " + fb["feedback"] for fb in feed_month]
        feed_month = "\n---\n".join(feed_month)

        print("feed_month\n", json.dumps(feed_month))
        
        chain = feedback_report()
        output = process_report(chain, data_str=json.dumps(feed_month))

        # store report
        report_collection = db["qualtrics_feedback_reports"]
        id_date = datetime(request_data.year, request_data.month, calendar.monthrange(request_data.year, request_data.month)[1])

        output = output.model_dump()
        output.update({"date": id_date})
        output.update({"source_qualtrics": source_dept})

        del_before = id_date - relativedelta(months=1)
        del_after = id_date + relativedelta(months=1)

        if request_data.delete_report:
            res_del = delete_data_between_dates(db[report_dest], del_before, del_after, "data")
            print("Deleted number of rows: ", res_del)

        insert_result = insert_data(db[report_dest], output)

        return {"inserted_id": "ok"}

    except Exception as e:
        e.add_note(f"Error api report: {e}")
        raise
    finally:
        if client:
            client.close()


@feedback_router.get("/report/{report_source}/{source_dept}", status_code=status.HTTP_200_OK)
async def feedback_report_api(
    year: int = Query(2, description="Year of report."),
    month: int = Query(2, description="Month of report."),
    report_source: str = Path(..., title="Report collection in mongodb"),
    source_dept: str = Path(..., title="Report collection in mongodb")
):
    try:
        today = date.today()
        if year > today.year:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid Year!")
        elif year == today.year and month > today.month:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid Month!")
        elif month < 1 or month > 12:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid Month!")
        
        db, collection, client = connect_to_collection(uri_feedback, db_feedback, report_source)

        report_month = get_data_by_year_month(collection=collection, year=year, month=month, date_field="date", project={'_id': 0}, filter_dict={"source_qualtrics": source_dept})

        return report_month

    except Exception as e:
        e.add_note(f"Error portal da queixa report: {e}")
        raise
    finally:
        if client:
            client.close()


@feedback_router.get("/latest-timestamp/{source}", status_code=status.HTTP_200_OK)
async def latest_timestamp(source: str = Path(..., title="Collection in mongodb")):
    try:
        _, collection, client = connect_to_collection(uri_feedback, db_feedback, source)

        return get_max_timestamp(collection, "date")

    except Exception as e:
        e.add_note(f"Error get timestamp: {e}")
        raise
    finally:
        if client:
            client.close()


@feedback_router.get("/summary/needs-review/{collection_name}", status_code=status.HTTP_200_OK)
async def get_review_summary_api( # Renamed function
    collection_name: str = Path(..., title="Collection name in MongoDB")
    # date_sort_field: str = Query("date", description="Field to sort recent items by") # Optional: Make sort field configurable
) -> Dict[str, Any]: # Use Dict or define a Pydantic response model
    """
    Gets the counts and 10 most recent feedback items based on the
    'needs_review' status from the specified collection.
    """
    client = None
    # Assuming 'date' is the standard field for sorting recency
    date_sort_field = "date"

    try:
        if not collection_name or not collection_name.strip():
             raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Collection name cannot be empty.")

        try:
            db, collection, client = connect_to_collection(
                uri_feedback, db_feedback, collection_name, create_collection=False
            )
        except ValueError as e:
             raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Collection '{collection_name}' not found. Details: {e}")

        # Call the updated function
        summary_data = get_review_summary(collection, date_sort_field=date_sort_field)

        # Use jsonable_encoder to handle ObjectId and datetime serialization for the response
        return jsonable_encoder(summary_data)

    except HTTPException as http_exc:
         raise http_exc
    except Exception as e:
        print(f"Error getting review summary for {collection_name}: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Failed to get review summary: {type(e).__name__}")
    finally:
        if client:
            client.close()



@feedback_router.post("/upload/qualtrics_provedoria", status_code=status.HTTP_201_CREATED)
async def upload_qualtrics_provedoria_file(
    file: UploadFile = File(..., description="Excel file (.xlsx, .xls) containing Qualtrics Provedoria feedback."),
    delete_existing_data: bool = Form(False, description="If true, deletes existing data INCLUSIVE of the min and max dates found in the file before inserting.")
):
    """
    Uploads a Qualtrics Provedoria Excel file, processes it using the utility function,
    analyzes sentiment using LLM, and stores results in the 'qualtrics_feedback' collection.
    Optionally deletes data within the date range found in the file before insertion.
    """
    client = None
    target_collection_name = "qualtrics_feedback" # Define target collection

    try:
        # --- File Validation ---
        if not file.filename or not file.filename.lower().endswith((".xlsx", ".xls")):
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid file type. Only XLS/XLSX files are allowed.")

        content = await file.read()
        if not content:
             raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Uploaded file is empty.")

        # --- Call Utility Function for Excel Processing ---
        try:
            # Now captures min_date and max_date returned by the function
            max_date, min_date, processed_records = qualtrics_provdoria(content)

            if not isinstance(processed_records, list):
                 raise ValueError("Processing function did not return expected data structure.")
             # Check if dates were returned correctly (basic check)
            valid_dates = isinstance(min_date, (datetime, date)) and isinstance(max_date, (datetime, date))
            if not valid_dates:
                 raise ValueError(f"Warning: Invalid min_date ({type(min_date)}) or max_date ({type(max_date)}).")

        except Exception as e:
             print(f"Error calling qualtrics_provdoria: {e}")
             # Use 422 as the file content caused the processing error
             raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=f"Error processing file content: {e}")

        if not processed_records:
            # Handle empty list returned by the function
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="No valid feedback records found or processing failed (check file content and format).")
        # --- End Excel Processing Call ---


        # --- Prepare Data for Sentiment Analysis ---
        try:
             # Validate records against Pydantic model
             # Make sure FeedbackQuestionnaire aligns with dict structure in processed_records
             feedback_list = [FeedbackQuestionnaire(**record) for record in processed_records]
             feedback_pydantic_list = ListFeedbackQuestionnaire(list=feedback_list)
        except Exception as pydantic_error:
             print(f"Data validation error after processing: {pydantic_error}")
             raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=f"Error validating processed data structure: {pydantic_error}")
        # --------------------------------------


        # --- Perform Sentiment Analysis ---
        try:
             chain = feedback_sentiment_analyzer() # Get the sentiment analysis chain
             # Process in batches (e.g., 10)
             output_with_sentiment: ListFeedbackQuestionnaireSentiment = process_feedback_sentiment(chain, feedback_pydantic_list, 10)
             # Extract the list of dictionaries with sentiment included
             records_to_insert = output_with_sentiment.model_dump()["list"]
        except Exception as llm_error:
             print(f"LLM Sentiment Analysis Error: {llm_error}")
             raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Error during sentiment analysis: {llm_error}")
        # -------------------------------


        # --- Database Operations ---
        # Ensure db_feedback and uri_feedback are accessible here
        db, collection, client = connect_to_collection(uri_feedback, db_feedback, target_collection_name)

        # Optional: Delete existing data using INCLUSIVE min/max dates from the file
        # by adjusting dates passed to the EXCLUSIVE delete_data_between_dates function
        deleted_count=0
        if delete_existing_data:
            # --- ADJUSTED Date Calculation for INCLUSIVE Deletion ---
            # Ensure start is datetime at the beginning of the day
            if isinstance(min_date, date) and not isinstance(min_date, datetime):
                start_dt_inclusive = datetime.combine(min_date, time.min) # 00:00:00 on min_date
            else:
                start_dt_inclusive = min_date

            # Ensure end is datetime at the beginning of the *next* day
            if isinstance(max_date, date) and not isinstance(max_date, datetime):
                 end_dt_exclusive_next_day = datetime.combine(max_date, time.min) + timedelta(days=1) # 00:00:00 on day AFTER max_date
            else:
                 # Assume max_date is datetime, get its date part, add 1 day
                 end_dt_exclusive_next_day = datetime.combine(max_date.date(), time.min) + timedelta(days=1)

            # Pass dates adjusted for the EXCLUSIVE nature of delete_data_between_dates
            # Pass slightly BEFORE min_date for $gt start_date (to include min_date 00:00:00)
            start_dt_for_delete = start_dt_inclusive - timedelta(days=1)
            # Pass start of the day AFTER max_date for $lt end_date (to include all of max_date)
            end_dt_for_delete = end_dt_exclusive_next_day
            # --- END ADJUSTED Date Calculation ---

            try:
                 # Call the UNCHANGED delete_data_between_dates function
                 deleted_count = delete_data_between_dates(collection, start_dt_for_delete, end_dt_for_delete, "date")
                 print(f"Deleted {deleted_count} existing records >= {start_dt_inclusive} and < {end_dt_exclusive_next_day} from {target_collection_name}") # Log reflects effective range
            except Exception as del_err:
                 print(f"Error deleting existing data: {del_err}")
                 raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Failed to delete existing data: {del_err}")


        # Insert new data
        if records_to_insert:
            insert_result = insert_data(collection, records_to_insert)
            num_inserted = len(insert_result) if insert_result else 0
            # Use jsonable_encoder if insert_result contains ObjectIds, otherwise format simply
            min_date_str = min_date.isoformat() if isinstance(min_date, (datetime, date)) else "N/A"
            max_date_str = max_date.isoformat() if isinstance(max_date, (datetime, date)) else "N/A"
            return {
                "message": f"File processed successfully. Data range found: {min_date_str} to {max_date_str}.",
                "num_inserted_records": num_inserted,
                "deleted_count": deleted_count
            }
        else:
            # This case might indicate an issue with sentiment analysis returning nothing
            return {"message": "No processed records with sentiment to insert.", "num_inserted_records": 0}
        # -------------------------

    except HTTPException as http_exc:
         # Re-raise deliberate HTTP exceptions
         raise http_exc
    except Exception as e:
        # General error handling
        print(f"Error during file upload processing: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"An unexpected error occurred: {type(e).__name__}")
    finally:
        # Ensure client is closed if it was opened
        if client:
            client.close()

# Include the routers in the main app
app.include_router(feedback_router)

#find . -type d -name __pycache__ -exec rm -r {} \+

import os
import json
from datetime import date
from fastapi import FastAPI, APIRouter, HTTPException, status, Query
from fastapi.middleware.cors import CORSMiddleware
from typing import Optional
from src.utils.utils import string_to_date, subtract_n_months_and_get_first_day
from src.conn_utils.mongo_conn import InputPostPortalDaQuiexa, connect_to_collection, \
    insert_data, ListCollectionPortalDaQuixa, delete_data_between_dates, get_data_by_year_month
from src.utils.utils_portal_da_queixa import get_portal_da_queixa_feedback
from src.llm_utils.models import feedback_classifier_portal_da_queixa, process_feedback_portal_da_queixa, \
    feedback_report_portal_da_queixa, process_report_portal_da_queixa
from src.conn_utils.queries_portal_da_queixa import sentiment_pipeline_filter_last_date_gte, \
    total_negative_feedback_pipeline_filter_last_date_gte, \
        total_negative_by_area_pipeline_filter_last_date_gte, \
            total_negative_by_area_class_pipeline_filter_last_date_gte, \
                total_negative_by_area_class_topic_pipeline_filter_last_date_gte, \
                    total_urgente_pipeline_filter_last_date_gte


db_host = os.environ.get("MONGO_HOST")
db_user = os.environ.get("MONGO_PRINCIPAL_USER")
db_password = os.environ.get("MONGO_PRINCIPAL_PASSWORD")
db_feedback = os.environ.get("MONGO_DB_CUSTOMER_FEEDBACK")
db_collection_portal_da_queixa = os.environ.get("MONGO_COLLECTION_PORTAL_DA_QUEIXA")

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

@feedback_router.post("/portal-da-queixa/process", status_code=status.HTTP_201_CREATED)
async def process_portal_da_queixa(params: InputPostPortalDaQuiexa):

    print(params)

    try:
        collection, client = connect_to_collection(uri_feedback, db_feedback, db_collection_portal_da_queixa)

        if params.delete_feedback:
            res_del = delete_data_between_dates(collection, params.last_date, params.to_date, "data")
            print("Deleted number of rows: ", res_del)

        res = get_portal_da_queixa_feedback(params)
        if len(res.root) == 0:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="No Data from portal da queixa")

        chain = feedback_classifier_portal_da_queixa()
        output = process_feedback_portal_da_queixa(chain, res)

        if isinstance(output, ListCollectionPortalDaQuixa) and len(output.root) > 0:
            insert_result = insert_data(collection, output.model_dump())
        else:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid data format portal da queixa")

        if insert_result is None:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Data insertion failed portal da queixa")

        return {"num_inserted_ids": len(insert_result)}
        
    except Exception as e:
        e.add_note(f"Error portal da queixa process: {e}")
        raise
    finally:
        if client:
            client.close()


@feedback_router.get("/portal-da-queixa/summary", status_code=status.HTTP_200_OK)
async def summary_portal_da_queixa(
    num_last_months: Optional[int] = Query(2, description="Number of months to look back.")
):
    try:
        if num_last_months < 1:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Number of months invalid.")
        
        collection, client = connect_to_collection(uri_feedback, db_feedback, db_collection_portal_da_queixa)

        date_to_filter = subtract_n_months_and_get_first_day(num_of_months=num_last_months)

        total_sentiment = list(collection.aggregate(sentiment_pipeline_filter_last_date_gte(date_to_filter)))[0]

        if len(total_sentiment) < 1:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Sentiment empty.")
        
        total_neg_feed = list(collection.aggregate(total_negative_feedback_pipeline_filter_last_date_gte(date_to_filter)))[0]

        if len(total_neg_feed) < 1:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Neg Feedback empty.")
        
        total_neg_feed_area = list(collection.aggregate(total_negative_by_area_pipeline_filter_last_date_gte(date_to_filter)))[0]

        if len(total_neg_feed_area) < 1:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Neg Feedback by Area empty.")
        
        total_neg_feed_area_class = list(collection.aggregate(total_negative_by_area_class_pipeline_filter_last_date_gte(date_to_filter)))[0]

        if len(total_neg_feed_area_class) < 1:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Neg Feedback by Area and class empty.")

        total_neg_feed_area_class_topic = list(collection.aggregate(total_negative_by_area_class_topic_pipeline_filter_last_date_gte(date_to_filter)))[0]

        if len(total_neg_feed_area_class_topic) < 1:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Neg Feedback by Area, class and topic empty.")
        
        total_urgent = list(collection.aggregate(total_urgente_pipeline_filter_last_date_gte(date_to_filter)))[0]

        if len(total_urgent) < 1:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Total urgent feedback empty.")
        
        return {
            "total_sentiment": total_sentiment["total_sentiment"],
            "sentiment_by_month": total_sentiment["sentiment_by_month"],
            "total_negative_feed_count": total_neg_feed["total_negative_count"][0]["count"],
            "total_negative_feed_by_month": total_neg_feed["negative_by_month"],
            "total_negative_feed_area_count": total_neg_feed_area["total_negative_by_area"],
            "top10_negative_feed_area_by_month": total_neg_feed_area["top10_negative_by_month_area"],
            "total_negative_feed_area_class_count": total_neg_feed_area_class["total_negative_by_area_class"],
            "top10_negative_feed_area_class_by_month": total_neg_feed_area_class["top10_negative_by_month_area_class"],
            "total_negative_feed_area_class_topic_count": total_neg_feed_area_class_topic["total_negative_by_area_class_topic"],
            "top10_negative_feed_area_class_topic_by_month": total_neg_feed_area_class_topic["top10_negative_by_month_area_class_topic"],
            "total_urgent_count": total_urgent["total_urgent_count"][0]["count"],
            "total_urgent_count_by_month": total_urgent["urgent_by_month"]
        }


    except Exception as e:
        e.add_note(f"Error portal da queixa summary: {e}")
        raise
    finally:
        if client:
            client.close()


@feedback_router.get("/portal-da-queixa/report", status_code=status.HTTP_201_CREATED)
async def report_portal_da_queixa(
    year: Optional[int] = Query(..., description="Report year."),
    month: Optional[int] = Query(..., ge=1, le=12, description="Report month.")
):
    try:
        today = date.today()
        if year > today.year:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid Year!")
        elif year == today.year and month > today.month:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid Month!")
        elif month < 1 and month > 12:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid Month!")
        
        collection, client = connect_to_collection(uri_feedback, db_feedback, db_collection_portal_da_queixa)
        feed_month = get_data_by_year_month(collection, year, month)
        chain = feedback_report_portal_da_queixa()
        output = process_report_portal_da_queixa(chain, json.dumps(feed_month))

        return output

    except Exception as e:
        e.add_note(f"Error portal da queixa report: {e}")
        raise
    finally:
        if client:
            client.close()






# Include the routers in the main app
app.include_router(feedback_router)

#find . -type d -name __pycache__ -exec rm -r {} \+

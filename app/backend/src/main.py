import os
import json
from datetime import datetime, date
from dateutil.relativedelta import relativedelta
from fastapi import FastAPI, APIRouter, HTTPException, status, Query, Path
from fastapi.middleware.cors import CORSMiddleware
from typing import Optional
from src.utils.utils import subtract_n_months_and_get_first_day
from src.conn_utils.mongo_conn import InputPostPortalDaQuiexa, connect_to_collection, \
    insert_data, ListCollectionPortalDaQuixa, delete_data_between_dates, get_data_by_year_month, \
        get_max_timestamp, InputReport, get_collection_unique_timestamps
from src.utils.utils_portal_da_queixa import get_portal_da_queixa_feedback
from src.llm_utils.models import feedback_classifier_portal_da_queixa, process_feedback_portal_da_queixa, \
    feedback_report, process_report
from src.conn_utils.queries_portal_da_queixa import results_total_by_month_filter_last_date_gte


db_host = os.environ.get("MONGO_HOST")
db_user = os.environ.get("MONGO_PRINCIPAL_USER")
db_password = os.environ.get("MONGO_PRINCIPAL_PASSWORD")
db_feedback = os.environ.get("MONGO_DB_CUSTOMER_FEEDBACK")
db_collection_portal_da_queixa = os.environ.get("MONGO_COLLECTION_PORTAL_DA_QUEIXA")
db_collection_portal_da_queixa_reports = os.environ.get("MONGO_COLLECTION_PORTAL_DA_QUEIXA_REPORTS")
db_collection_qualtrics_chatbot = os.environ.get("MONGO_COLLECTION_QUALTRICS_CHATBOT")
db_collection_qualtrics_chatbot_reports = os.environ.get("MONGO_COLLECTION_QUALTRICS_CHATBOT_REPORTS")

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
        _, collection, client = connect_to_collection(uri_feedback, db_feedback, db_collection_portal_da_queixa)

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
        
        _, collection, client = connect_to_collection(uri_feedback, db_feedback, db_collection_portal_da_queixa)

        date_to_filter = subtract_n_months_and_get_first_day(num_of_months=num_last_months)

        res_total = list(collection.aggregate(results_total_by_month_filter_last_date_gte(date_to_filter)))

        if len(res_total) < 1:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="results total empty.")
        
        return res_total


    except Exception as e:
        e.add_note(f"Error portal da queixa summary: {e}")
        raise
    finally:
        if client:
            client.close()


@feedback_router.get("/{source}/latest-timestamp", status_code=status.HTTP_200_OK)
async def latest_timestamp(source: str = Path(..., title="Collection in mongodb")):
    try:
        _, collection, client = connect_to_collection(uri_feedback, db_feedback, source)

        return get_max_timestamp(collection, "data")

    except Exception as e:
        e.add_note(f"Error get timestamp: {e}")
        raise
    finally:
        if client:
            client.close()


@feedback_router.get("/{source}/list-timestamp", status_code=status.HTTP_200_OK)
async def list_timestamp(source: str = Path(..., title="Collection in mongodb")):
    try:
        _, collection, client = connect_to_collection(uri_feedback, db_feedback, source)

        return get_collection_unique_timestamps(collection)

    except Exception as e:
        e.add_note(f"Error list timestamp: {e}")
        raise
    finally:
        if client:
            client.close()


@feedback_router.get("/{source}/report", status_code=status.HTTP_200_OK)
async def feedback_report_api(
    year: int = Query(2, description="Year of report."),
    month: int = Query(2, description="Month of report."),
    source: str = Path(..., title="Report collection in mongodb")
):
    try:
        today = date.today()
        if year > today.year:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid Year!")
        elif year == today.year and month > today.month:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid Month!")
        elif month < 1 or month > 12:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid Month!")
        
        db, collection, client = connect_to_collection(uri_feedback, db_feedback, source + "_reports")

        report_month = get_data_by_year_month(collection, year, month, "data", {'$project': {'_id': 0}})[0]

        return report_month

    except Exception as e:
        e.add_note(f"Error portal da queixa report: {e}")
        raise
    finally:
        if client:
            client.close()

@feedback_router.post("/{source}/process-report", status_code=status.HTTP_201_CREATED)
async def process_report_api(
    request_data: InputReport,
    source: str = Path(..., title="Feedbacks collection in mongodb")
    ):
    try:
        today = date.today()
        if request_data.year > today.year:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid Year!")
        elif request_data.year == today.year and request_data.month > today.month:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid Month!")
        elif request_data.month < 1 or request_data.month > 12:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid Month!")

        # create report
        if source == db_collection_portal_da_queixa:
            date_field = "data"
            projection = {'$project': {'_id': 0, 'resumo': 1}}
            report_collection = db_collection_portal_da_queixa_reports
        elif source == db_collection_qualtrics_chatbot:
            date_field = "data"
            projection = {'$project': {'_id': 0, 'str_list_feedbacks': 1}}
            report_collection = db_collection_qualtrics_chatbot_reports
        else:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid collection!")

        db, collection, client = connect_to_collection(uri_feedback, db_feedback, source)
        feed_month = get_data_by_year_month(collection=collection, date_field=date_field, month=request_data.month, year=request_data.year, project=projection)
        chain = feedback_report()
        output = process_report(chain, data_str=json.dumps(feed_month))

        # store report
        report_collection = db[report_collection]
        id_date = datetime(request_data.year, request_data.month, 1)

        output = output.model_dump()
        output.update({"data": id_date})

        day_before = id_date - relativedelta(days=1)
        day_after = id_date + relativedelta(days=1)

        if request_data.delete_report:
            res_del = delete_data_between_dates(report_collection, day_before, day_after, "data")
            print("Deleted number of rows: ", res_del)

        insert_result = insert_data(report_collection, output)

        return {"inserted_id": "ok"}

    except Exception as e:
        e.add_note(f"Error api report: {e}")
        raise
    finally:
        if client:
            client.close()



# Include the routers in the main app
app.include_router(feedback_router)

#find . -type d -name __pycache__ -exec rm -r {} \+

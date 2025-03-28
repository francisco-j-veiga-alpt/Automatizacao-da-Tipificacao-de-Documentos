import os
from fastapi import FastAPI, APIRouter, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from typing import Union
from src.llm_utils.models import feedback_classifier_generic, process_feedback_generic
from src.conn_utils.mongo_conn import connect_to_collection, insert_data, delete_data_between_dates, InputProcessBase,\
    InputProcessPortalDaQueixa, get_classifications_as_string
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
db_collection_customers_feedback = os.environ.get("MONGO_COLLECTION_CUSTOMERS_FEEDBACK")

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







# Include the routers in the main app
app.include_router(feedback_router)

#find . -type d -name __pycache__ -exec rm -r {} \+

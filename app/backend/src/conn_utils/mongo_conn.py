from pymongo import MongoClient
from pydantic import BaseModel, Field, field_validator, model_validator
from typing import List, Dict, Optional
from datetime import timedelta, datetime, time, date


class InputProcessBase(BaseModel):
    to_date: Optional[datetime] = Field(
        default_factory=lambda: datetime.combine(datetime.today().date(), time.min),
        description="Get feedback until to_date (exclusive)"
    )
    last_date: Optional[datetime] = Field(
        default_factory=lambda: datetime.combine(datetime.today().date(), time.min) - timedelta(2),
        description="Last date feedback was processed (inclusive)"
    )
    delete_feedback: bool = Field(
        False, description="Delete any existing feedback prior to insertion between dates"
    )

    @model_validator(mode="after")
    def check_date_relationship(cls, values: "InputProcessBase"):
        if values.last_date is not None and values.to_date is not None:
            if values.to_date <= values.last_date + timedelta(days=1):
                raise ValueError("to_date must be greater than last_date + 1 day")
        return values

class InputProcessPortalDaQueixa(InputProcessBase):
    begin_pages_to_look: int = Field(description="Page number in website to start scraping"),
    num_of_pages_to_look: int = Field(description="Number of pages to look after beginning page")

class Feedback(BaseModel):
    date: datetime = Field(description="Date of the feedback")
    user_id: str = Field(description="User's unique identfier e.g. on the platform")
    feedback_full_text: str = Field(description="Complete text of the feedback in Portuguese.")
    source: str = Field(description="Source of feedback")

class FeedbackClassification(Feedback):
    feedback_summary: str = Field(None, description="Summary of the feedback in Portuguese")
    classification: str = Field(description="Main classification of the feedback")
    sentiment: str = Field(description="Sentiment expressed in the feedback ('very positive', 'positive', 'very negative', 'negative', or 'neutral').")

    @field_validator("sentiment")
    def sentiment_must_be_valid(cls, value):
        if value not in ['Very Positive', 'Positive', 'Very Negative', 'Negative', 'Neutral']:
            raise ValueError("Sentiment must be 'Very Positive', 'Positive', 'Very Negative', 'Negative', or 'Neutral'")
        return value.title()


class ListFeedback(BaseModel):
    list: List[Feedback]

class ListFeedbackClassification(BaseModel):
    list: List[FeedbackClassification]

def connect_to_collection(conn_str, db_name, collection_name, create_collection=False):
    try:
        client = MongoClient(conn_str)
        db = client[db_name]
        if not collection_name in db.list_collection_names() and not create_collection:
            raise ValueError(f"Collection '{collection_name}' does not exist.")
        collection = db[collection_name]
        return db, collection, client
    except Exception as e:
        raise Exception(f"MongoDB connection error: {e}")

def insert_data(collection, data: List[Dict] | Dict):
    try:
        if isinstance(data, list):
            result = collection.insert_many(data)
            return [str(res) for res in result.inserted_ids]
        else:
            result = collection.insert_one(data)
            return [str(result.inserted_id)]
    except Exception as e:
        raise Exception(f"Error inserting data: {e}")

def delete_data_between_dates(collection, start_date, end_date, date_field):
    try:
        query = {date_field: {"$gt": start_date, "$lt": end_date}}
        result = collection.delete_many(query)
        return result.deleted_count
    except Exception as e:
        raise Exception(f"Error deleting data between dates: {e}")

def get_data_between_dates(collection, start_date, end_date, date_field):

    try:
        if not (isinstance(start_date, datetime) and isinstance(start_date, datetime)) :
            raise ValueError("start_date + delta 1 must be earlier than end_date.")

        if start_date + timedelta(days=1) >= end_date:
            raise ValueError("start_date + delta 1 must be earlier than end_date.")
        
        query = {
            date_field: {"$gt": start_date, "$lt": end_date}
        }

        result = collection.find(query)
        return result
        
    except Exception as e:
        e.add_note(f"An error occurred when deleting data: {e}")
        raise

def get_classifications_as_string(collection: str) -> str:
    try:
        # Query all documents in the collection
        documents = collection.find({}, {"classifications": 1, "_id": 0})

        # Extract 'classifications' field and create a newline-separated string
        classifications_list = [doc["classifications"] for doc in documents if "classifications" in doc]
        classifications_string = "\n".join(classifications_list)

        return classifications_string

    except Exception as e:
        raise Exception(f"Error retrieving classifications: {e}")

def get_data_by_year_month(collection, year, month, date_field, project):
    try:
        today = date.today()
        if year > today.year:
            raise ValueError("Invalid Year!")
        elif year == today.year and month > today.month:
            raise ValueError("Invalid Month!")
        elif month < 1 and month > 12:
            raise ValueError("Invalid Month!")

        start_date = datetime(year, month, 1)
        if month == 12:
            end_date = datetime(year + 1, 1, 1)
        else:
            end_date = datetime(year, month + 1, 1)

        pipeline = [
            {
                '$match': {
                    date_field: {
                        '$gte': start_date,
                        '$lt': end_date
                    }
                }
            },
            {
                '$sort': {date_field: 1}
            }, project
        ]

        return list(collection.aggregate(pipeline))
    except Exception as e:
        e.add_note(f"Get monthly feedback error: {e}")
        raise


def get_max_timestamp(collection, field):
    try:
        ts = collection.aggregate([

            {
                "$group": {
                    "_id": None,
                    "maxTimestamp": { "$max": f"${field}" }
                }
            }
        ]).next()["maxTimestamp"]
        return str(ts)
    except Exception as e:
        e.add_note(f"Error get timestamp: {e}")
        raise


def get_collection_unique_timestamps(collection, date_field_name="data", format_string="%Y-%m"):
    try:
        pipeline = [
            {
            "$group": {
                "_id": {
                "$dateToString": {
                    "format": format_string,
                    "date": "$data"
                }
                }
            }
            },
            { 
            "$sort": { 
                "_id": -1 
            } 
            },
            {
            "$group": {
                "_id": None,
                "dates": {
                "$push": "$_id"
                }
            }
            },
            {
            "$project": {
                "_id": 0,
                "dates": 1
            }
            }
        ]

        results = collection.aggregate(pipeline)
        result = next(results, None)
        if result:
            return result["dates"]
        else:
            return []  # Return an empty list if no results

    except Exception as e:
        e.add_note(f"An error occurred coll unique timestamps!: {e}")
        raise

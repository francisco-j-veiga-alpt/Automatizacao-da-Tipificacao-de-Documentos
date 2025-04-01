# src/conn_utils/mongo_conn.py
from pymongo import MongoClient
from pydantic import BaseModel, Field, field_validator, model_validator
from typing import List, Dict, Optional
from datetime import timedelta, datetime, time, date
import calendar # Added for potential use elsewhere, keep if needed

class InputProcessBase(BaseModel):
    to_date: Optional[datetime] = Field(
        default_factory=lambda: datetime.combine(datetime.today().date(), time.min),
        description="Get feedback until to_date (exclusive)"
    )
    last_date: Optional[datetime] = Field(
        default_factory=lambda: datetime.combine(datetime.today().date(), time.min) - timedelta(days=2),
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
    feedback_summary: str = Field(description="Summary of the feedback in Portuguese")
    classification: str = Field(description="Main classification of the feedback")
    sentiment: str = Field(description="Sentiment expressed in the feedback ('Very Positive', 'Positive', 'Very Negative', 'Negative', or 'Neutral').")
    needs_review: bool = Field(False, description="Flag indicating if the classification is uncertain or needs manual review.")

    @field_validator("sentiment")
    def sentiment_must_be_valid(cls, value):
        if value is not None and value not in ['Very Negative', 'Negative', 'Neutral', 'None']:
            raise ValueError("Sentiment must be 'Very Negative', 'Negative', or 'Neutral'")
        return value


class ListFeedback(BaseModel):
    list: List[Feedback]

class ListFeedbackClassification(BaseModel):
    list: List[FeedbackClassification]

# --- Database Connection and Operations ---

def connect_to_collection(conn_str, db_name, collection_name, create_collection=False):
    try:
        client = MongoClient(conn_str)
        db = client[db_name]
        # Ensure collection exists if not creating
        if not create_collection and collection_name not in db.list_collection_names():
             raise ValueError(f"Collection '{collection_name}' does not exist in database '{db_name}'.")
        collection = db[collection_name]
        return db, collection, client
    except Exception as e:
        raise Exception(f"MongoDB connection error: {e}")

def insert_data(collection, data: List[Dict] | Dict):
    try:
        if not data: # Handle empty data list
             return []
        if isinstance(data, list):
            # Ensure data is a list of dicts for insert_many
            if not all(isinstance(item, dict) for item in data):
                 raise TypeError("Data must be a list of dictionaries for insert_many.")
            result = collection.insert_many(data)
            return [str(res) for res in result.inserted_ids]
        elif isinstance(data, dict):
            result = collection.insert_one(data)
            return [str(result.inserted_id)]
        else:
            raise TypeError("Data must be a dictionary or a list of dictionaries.")
    except Exception as e:
        # Provide more context in error message
        raise Exception(f"Error inserting data into collection '{collection.name}': {e}")


def delete_data_between_dates(collection, start_date: datetime, end_date: datetime, date_field: str):
    try:
        if not isinstance(start_date, datetime) or not isinstance(end_date, datetime):
            raise TypeError("start_date and end_date must be datetime objects.")
        if start_date >= end_date:
             # Allow deletion up to the end_date boundary if needed, adjust logic if strict < is required
             raise TypeError(f"Error: start_date ({start_date}) is not before end_date ({end_date}). No data will be deleted unless they are exactly equal and query uses $lte/$gte.")
             # If deletion should occur only for dates strictly between, the query is correct.
             # If deletion should include start_date or end_date, adjust the query ($gte, $lte).

        # Original query: strictly between start_date and end_date
        # query = {date_field: {"$gt": start_date, "$lt": end_date}}
        # Query including start_date and up to (but not including) end_date:
        query = {date_field: {"$gt": start_date, "$lt": end_date}}

        result = collection.delete_many(query)
        return result.deleted_count
    except Exception as e:
        raise Exception(f"Error deleting data between dates in collection '{collection.name}': {e}")

# get_data_between_dates remains useful for fetching data
def get_data_between_dates(collection, start_date: datetime, end_date: datetime, date_field: str):
    try:
        if not (isinstance(start_date, datetime) and isinstance(start_date, datetime)) :
            raise ValueError("start_date + delta 1 must be earlier than end_date.")

        if start_date + timedelta(days=1) >= end_date:
            raise ValueError("start_date + delta 1 must be earlier than end_date.")
        
        query = {
            date_field: {"$gt": start_date, "$lt": end_date}
        }

        result = collection.find(query)
        return list(result) # Return as list for easier handling, adjust if cursor is needed

    except Exception as e:
        # Add note is deprecated, use standard exception chaining if needed or just raise
        raise Exception(f"An error occurred when getting data between dates: {e}")


def get_classifications_as_string(collection) -> str:
    try:
        # Query all documents, projecting only the 'classifications' field
        documents = collection.find({}, {"classifications": 1, "_id": 0})

        # Extract 'classifications' field and handle potential missing field
        classifications_list = [doc.get("classifications", "") for doc in documents] # Use .get for safety
        # Filter out empty strings if a document didn't have the field
        classifications_list = [c for c in classifications_list if c]

        if not classifications_list:
             # Raise error or return empty string depending on desired behavior
             raise ValueError(f"No documents with 'classifications' field found in collection '{collection.name}'.")

        classifications_string = "\n".join(classifications_list)

        return classifications_string

    except Exception as e:
        raise Exception(f"Error retrieving classifications from collection '{collection.name}': {e}")


# Other utility functions (get_data_by_year_month, get_max_timestamp, etc.) remain the same
# ... (keep existing functions like get_data_by_year_month, get_max_timestamp, get_collection_unique_timestamps)
def get_data_by_year_month(collection, year, month, date_field, project):
    try:
        today = date.today()
        if not (isinstance(year, int) and isinstance(month, int)):
            raise TypeError("Year and month must be integers.")
        if year > today.year or (year == today.year and month > today.month):
            raise ValueError("Invalid Year/Month (cannot be in the future).")
        if not 1 <= month <= 12:
            raise ValueError("Invalid Month (must be between 1 and 12).")

        # Calculate start and end dates for the given month
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
                        '$lt': end_date # Use $lt for the end date (exclusive)
                    }
                }
            },
            {
                '$sort': {date_field: 1} # Sort by date
            }
            # Add projection stage if provided
        ]
        if project:
             pipeline.append({'$project': project})


        return list(collection.aggregate(pipeline))
    except Exception as e:
        # Add note is deprecated
        raise Exception(f"Get monthly feedback error: {e}")


def get_max_timestamp(collection, field):
    try:
        # Ensure the field exists for aggregation
        # This query assumes at least one document has the field
        result = list(collection.aggregate([
            { "$match": { field: { "$exists": True } } }, # Ensure field exists
            {
                "$group": {
                    "_id": None,
                    "maxTimestamp": { "$max": f"${field}" }
                }
            },
            { "$project": { "_id": 0, "maxTimestamp": 1 } }
        ]))

        if result:
            ts = result[0].get("maxTimestamp")
            # Handle potential None if no documents have the field after $match
            return str(ts) if ts is not None else None
        else:
            # No documents found or field doesn't exist
            return None
    except Exception as e:
        # Add note is deprecated
        raise Exception(f"Error getting max timestamp for field '{field}': {e}")


def get_collection_unique_timestamps(collection, date_field_name="date", format_string="%Y-%m"): # Changed default field name
    try:
        pipeline = [
             { "$match": { date_field_name: { "$exists": True } } }, # Ensure date field exists
            {
            "$group": {
                "_id": {
                "$dateToString": {
                    "format": format_string,
                    "date": f"${date_field_name}" # Use variable for field name
                }
                }
            }
            },
            {
            "$sort": {
                "_id": -1 # Sort descending (most recent first)
            }
            },
            {
            "$project": {
                 "date_str": "$_id", # Rename _id for clarity
                 "_id": 0
             }
            },
             # Optional: Group into a single array if needed, otherwise return list of date strings
             {
                 "$group": {
                     "_id": None,
                     "dates": { "$push": "$date_str" }
                 }
             },
             { "$project": { "_id": 0, "dates": 1 } }
        ]

        results = list(collection.aggregate(pipeline)) # Execute pipeline

        if results:
            # If grouped into a single array:
            return results[0].get("dates", [])
            # If not grouped, results will be list of dicts like [{"date_str": "2023-10"}, ...]
            # return [item["date_str"] for item in results]
        else:
            return []  # Return an empty list if no results

    except Exception as e:
        # Add note is deprecated
        raise Exception(f"An error occurred getting collection unique timestamps: {e}")
# src/conn_utils/mongo_conn.py

from pymongo import MongoClient, DESCENDING
from pydantic import BaseModel, Field, field_validator, model_validator
from typing import List, Dict, Optional, Any # Added Optional and Any
from datetime import timedelta, datetime, time, date
import calendar # Added for potential use elsewhere, keep if needed

class InputProcessBase(BaseModel):
    to_date: Optional[datetime] = Field(
        default_factory=lambda: datetime.combine(datetime.today().date(), time.min),
        description="Get feedback until to_date (exclusive)"
    )
    last_date: Optional[datetime] = Field(
        default_factory=lambda: datetime.combine(datetime.today().date(), time.min) - timedelta(days=2),
        description="Last date feedback was processed (exclusive)"
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
    sentiment: str = Field(description="Sentiment expressed in the feedback ('Very Negative', 'Negative', or 'Neutral').")
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



# --- New Model for Questionnaire Feedback Sentiment Analysis ---

class FeedbackQuestionnaire(BaseModel):
    """
    Model representing the structure of a single customer feedback entry
    originating from a post-case handling questionnaire, used specifically
    for sentiment analysis.
    """
    date: datetime = Field(description="The exact date when the feedback questionnaire was submitted.")
    id_source: str = Field(description="Unique identifier for the feedback entry, often from the source system (e.g., CRM ticket ID related to the original case).")
    source: str = Field(description="The origin or platform from which the questionnaire feedback was collected (e.g., 'Qualtrics', 'SurveyMonkey').")
    crm_classification: str = Field(description="The classification assigned to the original case/ticket in the CRM system that this questionnaire feedback relates to.")
    feedback: str = Field(description="The verbatim text of the customer's answer to the open-ended question in the questionnaire, specifically 'O que podera a MEO fazer para melhorar o atendimento?'.")
    source_qualtrics: str = Field(description="") # TODO: chage later to source_questionnaire

class FeedbackQuestionnaireSentiment(FeedbackQuestionnaire):
    # Corrected: Changed str to Optional[str]
    sentiment: Optional[str] = Field(description="Sentiment: 'Very Negative', 'Negative', 'Neutral', or null.")

    @field_validator("sentiment")
    def sentiment_must_be_valid(cls, value):
        # This validator already correctly handles None, so no change needed here.
        allowed_sentiments = {'Very Negative', 'Negative', 'Neutral', None}
        if value not in allowed_sentiments:
            print(f"Warning: Unexpected sentiment value '{value}' received.")
            # Depending on strictness, you might raise ValueError here
        return value

class ListFeedbackQuestionnaireSentiment(BaseModel):
    list: List[FeedbackQuestionnaireSentiment]

class ListFeedbackQuestionnaire(BaseModel):
    list: List[FeedbackQuestionnaire]


class InputReport(BaseModel):
    year: int
    month: int
    delete_report: bool = False


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
def get_data_by_year_month(
    collection,
    year: int,
    month: int,
    date_field: str,
    project: Optional[Dict] = None, # Keep existing project param
    filter_dict: Optional[Dict] = None # Add new optional filter parameter
    ):
    """
    Retrieves data from a MongoDB collection for a specific year and month,
    optionally applying additional filters and projection.

    Args:
        collection: The pymongo collection object.
        year: The year to filter by.
        month: The month to filter by (1-12).
        date_field: The name of the field containing date information.
        project: Optional dictionary defining a $project stage.
        filter_dict: Optional dictionary of additional key-value pairs to add to the $match stage.

    Returns:
        A list of documents matching the criteria.
    """
    try:
        # --- Input validation remains the same ---
        today = date.today()
        if not (isinstance(year, int) and isinstance(month, int)):
            raise TypeError("Year and month must be integers.")
        if year > today.year or (year == today.year and month > today.month):
            raise ValueError("Invalid Year/Month (cannot be in the future).")
        if not 1 <= month <= 12:
            raise ValueError("Invalid Month (must be between 1 and 12).")
        # ----------------------------------------

        # Calculate start and end dates for the given month
        start_date = datetime(year, month, 1)
        # Calculate end date correctly (first moment of the next month)
        if month == 12:
            end_date = datetime(year + 1, 1, 1)
        else:
            end_date = datetime(year, month + 1, 1)

        # --- Build the $match stage ---
        match_stage_filter = {
            date_field: {
                '$gte': start_date,
                '$lt': end_date # Use $lt for exclusive end date
            }
        }
        # Add additional filters if provided
        if filter_dict and isinstance(filter_dict, dict):
            match_stage_filter.update(filter_dict) # Merge the filter_dict
        # ---------------------------

        # Construct the pipeline
        pipeline = [
            {
                '$match': match_stage_filter # Use the combined match criteria
            },
            {
                '$sort': {date_field: 1} # Sort by date
            }
        ]

        # Add projection stage if provided correctly
        if project and isinstance(project, dict):
             # Ensure it's added as a proper $project stage if not empty
             if project: # Check if project dict is not empty
                pipeline.append({'$project': project})

        return list(collection.aggregate(pipeline))

    # --- Keep existing error handling ---
    except TypeError as te:
         # Reraise type errors for clarity
         raise te
    except ValueError as ve:
         # Reraise value errors for clarity
         raise ve
    except Exception as e:
        # Handle other potential MongoDB or processing errors
        # Using print or proper logging instead of add_note
        print(f"Error retrieving monthly feedback: {e}")
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



def retrieve_grouped_sentiment_counts(
    collection,
    year: int,
    month: int,
    group_by_column: str = "classification",
    sentiment_column: str = "sentiment",
    group_level: Optional[int] = None, # Parameter for level selection
    filter_by_columns: Optional[Dict] = None,
    date_field: str = "date"
):
    """
    Retrieves data from MongoDB for a specific year and month, providing a
    per-group sentiment breakdown (with total count per group), an overall
    total sentiment count, and the query date string ("YYYY/MM").
    Allows grouping by a specific hierarchy level path.

    Args:
        collection: The pymongo collection object.
        year: The year to filter by.
        month: The month to filter by (1-12).
        group_by_column: The hierarchical field name for grouping.
        sentiment_column: The field name containing the sentiment values.
        group_level: Optional integer specifying the hierarchy level (1-based) path
                     to group by. If None or <= 0, groups by the full field value.
                     If the level is deeper than available, groups by the full available path.
        filter_by_columns: Optional dictionary of additional key-value pairs to filter by.
        date_field: The name of the field containing date information. Defaults to 'date'.

    Returns:
        A dictionary containing:
        - 'query_date': String representing the query period ("YYYY/MM").
        - 'total_sentiment': Overall sentiment counts.
        - 'grouping_summary': List of dictionaries, each with a 'grouping_value',
                              'group_total_count', and non-zero 'sentiment_counts_total'.
        Returns None if an error occurs or a default structure if no data matches.
    """
    try:
        if not (1 <= month <= 12):
            raise ValueError("Month must be between 1 and 12.")

        # Construct the query date string (YYYY/MM)
        query_date_str = f"{year}/{month:02d}"

        # Calculate start and end dates
        start_date = datetime(year, month, 1, 0, 0, 0)
        _, last_day = calendar.monthrange(year, month)
        end_date = datetime(year, month, last_day, 23, 59, 59, 999999)

        # --- Common Setup ---
        match_criteria = {
            date_field: {'$gte': start_date, '$lte': end_date},
            group_by_column: { '$exists': True, '$type': "string" }
        }
        if filter_by_columns:
            match_criteria.update(filter_by_columns)

        expected_sentiments = ['Very Negative', 'Negative', 'Neutral']

        # Helper to create sentiment sum expressions
        def create_sentiment_sums(prefix=""):
            sums = {}
            for sentiment_value in expected_sentiments:
                field_key = f"{prefix}count_{sentiment_value.replace(' ', '_')}"
                sums[field_key] = {
                    '$sum': {
                        '$cond': [{'$eq': [f'${sentiment_column}', sentiment_value]}, 1, 0]
                    }
                }
            return sums

        # --- Logic to Calculate Grouping Key (Path) Based on Level ---
        calculate_grouping_key_stage = {
            # ... (same $addFields logic as previous version) ...
             '$addFields': {
                'grouping_key': {
                    '$let': {
                        'vars': {
                            'full_key': f'${group_by_column}',
                            'levels': {'$split': [f'${group_by_column}', '>']},
                            'requested_level': group_level if group_level and group_level > 0 else 0
                        },
                        'in': {
                            '$cond': [
                                {'$gt': ['$$requested_level', 0]},
                                { # Level grouping requested
                                    '$let': {
                                        'vars': {
                                            'slice_count': { '$min': ['$$requested_level', {'$size': '$$levels'}] }
                                        },
                                        'in': {
                                            '$reduce': {
                                                'input': {'$slice': ['$$levels', '$$slice_count']},
                                                'initialValue': "",
                                                'in': {
                                                    '$cond': [ {'$eq': ['$$value', '']}, '$$this', {'$concat': ['$$value', '>', '$$this']} ]
                                                }
                                            }
                                        }
                                    }
                                },
                                '$$full_key' # No level grouping requested
                            ]
                        }
                    }
                }
            }
        }


        # --- Facet 1: Per Group Breakdown (Added group_total_count) ---
        classification_pipeline = [
            calculate_grouping_key_stage, # Calculate the key first
            {
                '$group': {
                    '_id': '$grouping_key', # Group by the calculated path
                    **create_sentiment_sums(),
                    # --- Add total count for the group ---
                    'group_total_count': { '$sum': 1 }
                    # -------------------------------------
                }
            },
            { # Project to reshape
                '$project': {
                    '_id': 0,
                    'grouping_value': '$_id', # Output the calculated path
                    # --- Include the group total count ---
                    'group_total_count': '$group_total_count',
                    # -----------------------------------
                    'sentiment_counts_total': {
                        '$arrayToObject': {
                            '$filter': {
                                'input': [
                                    {'k': sv, 'v': f"$count_{sv.replace(' ', '_')}"} for sv in expected_sentiments
                                ],
                                'as': 'pair',
                                'cond': {'$gt': ['$$pair.v', 0]}
                            }
                        }
                    }
                }
            },
            { # Remove groups where sentiment_counts_total is empty (optional, keeps groups with only 0 counts otherwise)
                '$match': {
                    'sentiment_counts_total': {'$ne': {}}
                }
            },
            { # Sort by the grouping value path
                '$sort': { 'grouping_value': 1 }
            }
        ]

        # --- Facet 2: Overall Totals (remains the same) ---
        overall_total_pipeline = [
             # ... (same as previous version) ...
             { '$group': { '_id': None, **create_sentiment_sums(prefix="total_") } },
             { '$project': { '_id': 0, 'total_sentiment': { sv: f"$total_count_{sv.replace(' ', '_')}" for sv in expected_sentiments } } }
        ]

        # --- Main Aggregation Pipeline with $facet ---
        pipeline = [
            { '$match': match_criteria },
            { '$facet': { 'grouping_summary': classification_pipeline, 'overall_totals_temp': overall_total_pipeline } },
            { # Reshape the $facet output
                '$project': {
                    '_id': 0,
                    'grouping_summary': '$grouping_summary',
                    'total_sentiment': {
                        '$ifNull': [
                             { '$arrayElemAt': ['$overall_totals_temp.total_sentiment', 0] },
                             { sentiment_value: 0 for sentiment_value in expected_sentiments }
                        ]
                    }
                }
            }
        ]

        # Execute the pipeline
        results = list(collection.aggregate(pipeline))

        # Default result structure
        default_result = {
            'query_date': query_date_str,
            'total_sentiment': { sentiment_value: 0 for sentiment_value in expected_sentiments },
            'grouping_summary': []
        }

        if results:
            final_result = results[0]
            final_result['query_date'] = query_date_str
            # Return potentially reordered keys
            return {
                'query_date': final_result.get('query_date'),
                'total_sentiment': final_result.get('total_sentiment', default_result['total_sentiment']),
                'grouping_summary': final_result.get('grouping_summary', default_result['grouping_summary'])
            }
        else:
             return default_result


    except ValueError as ve:
        print(f"Input validation error: {ve}")
        return None
    except Exception as e:
        print(f"An error occurred during aggregation: {e}")
        return None


def get_review_summary(collection, date_sort_field: str = "date") -> Dict[str, Any]:
    """
    Counts documents and retrieves the 10 most recent items (excluding _id)
    based on the boolean 'needs_review' field.

    Args:
        collection: The pymongo collection object.
        date_sort_field: The name of the date field to use for sorting recent items.

    Returns:
        A dictionary containing counts and lists of recent items. Documents
        in the lists will not contain the '_id' field. Other BSON types
        (like datetime) will remain and need handling by the caller (e.g., FastAPI's
        jsonable_encoder).
        Example: {
            "counts": {"needs_review_true": 10, "needs_review_false": 100},
            "recent_needs_review": [list_of_10_docs_true_without_id],
            "recent_does_not_need_review": [list_of_10_docs_false_without_id]
        }
    """
    try:
        # Get Counts
        count_true = collection.count_documents({"needs_review": True})
        count_false = collection.count_documents({"needs_review": False})

        # Define projection to exclude _id
        projection = {'_id': 0}

        # Get 10 Most Recent Items for needs_review: True, excluding _id
        recent_true_cursor = collection.find(
            {"needs_review": True},
            projection # Apply projection here
        ).sort(date_sort_field, DESCENDING).limit(10)
        recent_true_list = list(recent_true_cursor)

        # Get 10 Most Recent Items for needs_review: False, excluding _id
        recent_false_cursor = collection.find(
            {"needs_review": False},
            projection # Apply projection here
        ).sort(date_sort_field, DESCENDING).limit(10)
        recent_false_list = list(recent_false_cursor)

        # --- Removed manual serialization logic ---

        return {
            "counts": {
                "needs_review_true": count_true,
                "needs_review_false": count_false
            },
            # Return the lists fetched without _id
            "recent_needs_review": recent_true_list,
            "recent_does_not_need_review": recent_false_list
        }
    except Exception as e:
        print(f"Error getting review summary from collection '{collection.name}': {e}")
        raise Exception(f"Error getting review summary: {e}")
    

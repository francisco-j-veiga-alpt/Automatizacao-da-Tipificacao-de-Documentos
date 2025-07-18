import os
from pymongo import MongoClient
import json
from typing import Any, Dict


def get_env_variable(name: str, default: Any = None) -> Any:
    """
    Safely get an environment variable, with optional default.
    """
    return os.environ.get(name, default)


def get_mongo_client(uri: str) -> MongoClient:
    """
    Create and return a MongoDB client.
    """
    return MongoClient(uri)


def insert_documents(collection, documents):
    """
    Insert a list of documents into a MongoDB collection.
    Returns the insert result.
    """
    if isinstance(documents, dict):
        documents = [documents]
    return collection.insert_many(documents)


def serialize_for_json(data: Any) -> str:
    """
    Serialize data to a JSON string, handling non-serializable types.
    """
    def default(o):
        if hasattr(o, 'isoformat'):
            return o.isoformat()
        return str(o)
    return json.dumps(data, default=default)


def deserialize_from_json(data: str) -> Any:
    """
    Deserialize a JSON string to Python data.
    """
    return json.loads(data)


def get_mongo_collection(uri: str, db_name: str, collection_name: str):
    """
    Get a MongoDB collection object.
    """
    client = get_mongo_client(uri)
    db = client[db_name]
    return db[collection_name], client

# Add more helpers as needed for webscraping, LLM, etc. 
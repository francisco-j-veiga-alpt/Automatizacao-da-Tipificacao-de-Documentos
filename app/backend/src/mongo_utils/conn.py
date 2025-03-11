from pymongo import MongoClient
from pydantic import BaseModel
from typing import List

class User(BaseModel):
    name: str
    age: int
    city: str

class UsersList(BaseModel):
    users: List[User]

def connect_mongo(mongo_uri, database_name, collection_name):
    # Connect to MongoDB
    try:
        # Create a MongoClient object
        client = MongoClient(mongo_uri)

        # Access the database
        db = client[database_name]

        # Access the collection
        collection = db[collection_name]

        return client, db, collection

    except Exception as e:
        print(f"An error occurred connect_mongo: {e}")


def list_collection_mongo(collection, query={}, projection={'_id':0}):
    try:
        return list(collection.find(query, projection))
    except Exception as e:
        print(f"An error occurred list_users_mongo: {e}")

def add_users_to_collection(users, collection):

    try:

        # Insert users into the collection
        if isinstance(users, dict):  # Single user
            result = collection.insert_one(users)
            inserted_ids = len([result.inserted_id])
        elif isinstance(users, list):  # Multiple users
            result = collection.insert_many(users)
            inserted_ids = len(result.inserted_ids)
        else:
            raise ValueError("Input must be a dictionary (single user) or a list of dictionaries (multiple users).")

        print(f"Users added successfully. Inserted IDs: {inserted_ids}")
        return inserted_ids

    except Exception as e:
        print(f"An error occurred: {e}")
        return None


def get_data_from_collection(compras,collection):
    try:
        
        records = collection.find()
        data_list = list(records)
        
        if not data_list:
            print("Nenhums dado encontrado na coleção.")
            return []
        
        print(f"{len(data_list)} registros encontrados.")
        return data_list
    except Exception as e:
        print(f"Ocorreu um erro ao buscar os dados: {e}")
        return None

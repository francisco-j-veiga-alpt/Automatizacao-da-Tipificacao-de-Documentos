from pymongo import MongoClient
import time
import pymongo
import sys

print(f"Python version: {sys.version}")
print(f"PyMongo version: {pymongo.__version__}")

# Wait for MongoDB to initialize
print("Waiting for MongoDB to initialize...")
time.sleep(5)

def test_connection(uri, description):
    print(f"\nTesting {description} connection...")
    print(f"URI: {uri}")
    try:
        client = MongoClient(uri, serverSelectionTimeoutMS=5000)
        # Force a connection to verify it works
        server_info = client.server_info()
        print(f"Connection successful!")
        print(f"Server info: {server_info}")
        return client
    except Exception as e:
        print(f"Connection failed: {str(e)}")
        return None

# Test admin connection
admin_uri = "mongodb://admin:admin1234@127.0.0.1:27017/admin?authSource=admin"
admin_client = test_connection(admin_uri, "admin")

if admin_client:
    print("\nListing all databases:")
    try:
        dbs = admin_client.list_database_names()
        print(f"Available databases: {dbs}")
    except Exception as e:
        print(f"Failed to list databases: {str(e)}")

# Test user connection
user_uri = "mongodb://access_principal:access1234@127.0.0.1:27017/customer_feedback?authSource=admin"
user_client = test_connection(user_uri, "user")

if user_client:
    print("\nTesting customer_feedback database access:")
    try:
        db = user_client.customer_feedback
        collections = db.list_collection_names()
        print(f"Available collections: {collections}")
    except Exception as e:
        print(f"Failed to access collections: {str(e)}")
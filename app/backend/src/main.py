from fastapi import FastAPI, Request, Query
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from src.mongo_utils.conn import connect_mongo, list_collection_mongo, add_users_to_collection, UsersList
from typing import List, Dict

mongo_uri = "mongodb://admin:admin1234@mongo_db:27017"
db_sales = "db_sales"
coll_users = "users" 
coll_compras="compras"

app = FastAPI()

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

@app.get("/")
async def root():
    return {"message": "Hello World 222"}

@app.get("/list-users")
async def list_users(number: int = Query(30)):

    try:
        client, _, coll = connect_mongo(mongo_uri=mongo_uri, database_name=db_sales, collection_name=coll_users)

        res = list_collection_mongo(coll)

        return {"list": res[:number]}
    
    except Exception as e:
        print(f"An error occurred list_users: {e}")
    finally:
        client.close()

 
@app.post("/add-users")
async def create_item(request: Request):
    try:
        data = await request.json()
        client, _, coll = connect_mongo(mongo_uri=mongo_uri, database_name=db_sales, collection_name=coll_users)
        num_users = add_users_to_collection(data, coll)
        return {"num_users_sdded": num_users}
 
    except Exception as e:
        return JSONResponse(content={"error": str(e)}, status_code=500)
    finally:
        client.close()
    


@app.get("/list-compras")
async def list_compras():

    try:
        client, _, coll = connect_mongo(mongo_uri=mongo_uri, database_name=db_sales, collection_name=coll_compras)

        res = list_collection_mongo(coll)

        return {"list": res}

    except Exception as e:
        print(f"An error occurred list_compras: {e}")
    finally:
        client.close()


@app.post("/delete-user")
async def delete_user(request: Request):
    try:
        data = await request.json()
        client, _, coll = connect_mongo(mongo_uri=mongo_uri, 
                                      database_name=db_sales, 
                                      collection_name=coll_users)
        
        # Delete user by name
        result = coll.delete_one({"name": data["name"]})
        
        if result.deleted_count == 0:
            return JSONResponse(content={"error": "User not found"}, status_code=404)
            
        return {"message": "User deleted successfully"}
        
    except Exception as e:
        return JSONResponse(content={"error": str(e)}, status_code=500)
    finally:
        client.close()



@app.post("/update-user")
async def update_user(request: Request):
    try:
        data = await request.json()
        client, _, coll = connect_mongo(mongo_uri=mongo_uri, database_name=db_sales, collection_name=coll_users)

        # Find the user by name and update the details
        result = coll.update_one(
            {"name": data["name"]},  # Filter based on the user's current name
            {"$set": {
                "age": data["age"],
                "city": data["city"]
            }}
        )

        if result.modified_count == 0:
            return JSONResponse(content={"error": "User not found or data is the same"}, status_code=404)

        return {"message": "User updated successfully"}

    except Exception as e:
        return JSONResponse(content={"error": str(e)}, status_code=500)
    finally:
        client.close()

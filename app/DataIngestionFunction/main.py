import azure.functions as func
import azure.durable_functions as df

# Durable Functions v2 model app object
myApp = df.DFApp(http_auth_level=func.AuthLevel.ANONYMOUS)

# HTTP starter function to trigger the orchestration
@myApp.route(route="orchestrators/{functionName}")
@myApp.durable_client_input(client_name="client")
async def http_start(req: func.HttpRequest, client):
    function_name = req.route_params.get('functionName')
    # Accept input params from query or body
    params = req.params.get('params')
    if not params:
        try:
            req_body = req.get_json()
        except ValueError:
            req_body = {}
        params = req_body.get('params')
    if params:
        instance_id = await client.start_new(function_name, None, params)
        response = client.create_check_status_response(req, instance_id)
    else:
        response = func.HttpResponse("Please pass 'params' in the query string or body", status_code=400)
    return response

# Orchestrator function: chains the three activities
@myApp.orchestration_trigger(context_name="context")
def orchestrator_function(context):
    input_params = context.get_input()
    # Step 1: Webscraping (API + HTML)
    scraped_data = yield context.call_activity('webscraping_activity', input_params)
    # Step 2: Store in MongoDB
    mongo_result = yield context.call_activity('mongodb_store_activity', scraped_data)
    # Step 3: LLM report generation
    report = yield context.call_activity('llm_report_activity', mongo_result)
    return report

# Activity: Webscraping (API + HTML)
@myApp.activity_trigger(input_name="params")
def webscraping_activity(params):
    # TODO: Integrate get_portal_da_queixa_feedback or similar logic here
    # Example: feedback = get_portal_da_queixa_feedback(params)
    # For now, return dummy data
    return {"scraped_feedback": "dummy_feedback"}

# Activity: Store in MongoDB
@myApp.activity_trigger(input_name="scraped_data")
def mongodb_store_activity(scraped_data):
    # TODO: Integrate MongoDB storage logic here
    # Example: insert_data(collection, scraped_data)
    # For now, return dummy result
    return {"mongo_result": "dummy_inserted_data"}

# Activity: LLM report generation
@myApp.activity_trigger(input_name="mongo_result")
def llm_report_activity(mongo_result):
    # TODO: Integrate LLM report generation logic here
    # Example: report = process_report(chain, mongo_result)
    # For now, return dummy report
    return {"llm_report": "dummy_report"}

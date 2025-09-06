"""Example FastAPI application using FastQueue with callbacks."""
from fastapi import FastAPI
from fastqueue import task, Client
from fastqueue.patterns.nng_patterns import PairPattern
from fastqueue.tasks.models import TaskPriority
from fastqueue.tasks.serializer import TaskSerializer, SerializationFormat
import asyncio
import json

# Create FastAPI app
app = FastAPI(title="FastQueue Callback Example")

# Define a task
@task
def process_data(data: dict) -> dict:
    """Process some data."""
    print(f"Processing data: {data}")
    # Simulate some work
    import time
    time.sleep(2)
    return {"processed": True, "data": data}

# Global client instance
client = None

@app.on_event("startup")
async def startup_event():
    """Initialize FastQueue client on startup."""
    global client
    client = Client()
    await client.start()
    print("FastQueue client initialized")

@app.on_event("shutdown")
async def shutdown_event():
    """Clean up FastQueue client on shutdown."""
    global client
    if client:
        client.stop()
        print("FastQueue client stopped")

@app.post("/process_with_callback/")
async def process_with_callback(data: dict, callback_address: str):
    """Process data with a callback when finished."""
    if client:
        # Submit task with callback
        result = await client.delay_with_callback(
            "process_data", 
            callback_address, 
            data,
            callback_data={"source": "fastapi_example"}
        )
        
        if result.status == "success":
            return {"message": "Task submitted", "task_id": result.task_id}
        else:
            return {"error": result.error}
    else:
        return {"error": "FastQueue client not available"}

@app.post("/process_with_internal_callback/")
async def process_with_internal_callback(data: dict):
    """Process data with an internal callback listener."""
    if client:
        # Create a unique callback address for this request
        callback_address = f"tcp://127.0.0.1:{5000 + hash(str(data)) % 1000}"
        
        # Start callback listener
        callback_task = asyncio.create_task(listen_for_callback(callback_address))
        
        # Submit task with callback
        result = await client.delay_with_callback(
            "process_data", 
            callback_address, 
            data,
            callback_data={"source": "internal_callback", "endpoint": "/process_result/"}
        )
        
        if result.status == "success":
            return {"message": "Task submitted", "task_id": result.task_id, "callback_address": callback_address}
        else:
            return {"error": result.error}
    else:
        return {"error": "FastQueue client not available"}

async def listen_for_callback(callback_address: str):
    """Listen for callback notifications."""
    try:
        # Create a pair pattern to receive callbacks
        callback_listener = PairPattern(callback_address, is_server=True)
        await callback_listener.start()
        
        print(f"Listening for callbacks on {callback_address}")
        
        # Listen for one callback
        data = await callback_listener.recv()
        callback_data = TaskSerializer.deserialize(data, SerializationFormat.JSON)
        
        print(f"Received callback: {callback_data}")
        
        # Process the callback data (in a real app, you might update a database, 
        # send a WebSocket message, etc.)
        await process_callback_result(callback_data)
        
        callback_listener.close()
        
    except Exception as e:
        print(f"Error in callback listener: {e}")

async def process_callback_result(callback_data: dict):
    """Process the callback result."""
    print(f"Processing callback result: {callback_data}")
    # In a real application, you might:
    # - Update a database with the result
    # - Send a WebSocket message to the client
    # - Send an email notification
    # - Trigger another task
    # etc.

@app.get("/")
async def root():
    """Root endpoint."""
    return {"message": "FastQueue Callback Example"}

# To run this example:
# 1. Start one or more FastQueue workers in separate terminals:
#    fastqueue worker --worker-id worker1 --task-modules fastqueue.examples.tasks
#
# 2. Run this FastAPI application:
#    uvicorn fastqueue.examples.callback_example:app --reload
#
# 3. Make requests to the endpoints:
#    curl -X POST "http://127.0.0.1:8000/process_with_callback/?callback_address=tcp://127.0.0.1:5560" -H "Content-Type: application/json" -d '{"key": "value"}'
#    curl -X POST "http://127.0.0.1:8000/process_with_internal_callback/" -H "Content-Type: application/json" -d '{"key": "value"}'
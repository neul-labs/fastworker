"""Example FastAPI application using FastWorker."""

from fastapi import FastAPI, BackgroundTasks
from fastworker import task, Client
from fastworker.tasks.models import TaskPriority
import asyncio

# Create FastAPI app
app = FastAPI(title="FastWorker FastAPI Example")


# Define some tasks
@task
def process_user_registration(user_id: int, email: str) -> str:
    """Process user registration."""
    # Simulate some work
    print(f"Processing registration for user {user_id} with email {email}")
    return f"User {user_id} registered successfully"


@task
def send_notification(user_id: int, message: str) -> str:
    """Send notification to user."""
    # Simulate sending notification
    print(f"Sending notification to user {user_id}: {message}")
    return f"Notification sent to user {user_id}"


@task
async def async_data_processing(data: dict) -> dict:
    """Async data processing task."""
    print(f"Processing data: {data}")
    await asyncio.sleep(1)  # Simulate async work
    return {"status": "processed", "data": data}


# Global client instance
# (in a real app, you might want to manage this differently)
client = None


@app.on_event("startup")
async def startup_event():
    """Initialize FastWorker client on startup."""
    global client
    client = Client()
    await client.start()
    print("FastWorker client initialized")


@app.on_event("shutdown")
async def shutdown_event():
    """Clean up FastWorker client on shutdown."""
    if client:
        client.stop()
        print("FastWorker client stopped")


@app.post("/register_user/")
async def register_user(user_id: int, email: str, background_tasks: BackgroundTasks):
    """Register a new user."""
    # Submit task to FastWorker
    if client:
        # For immediate response, we can use FastAPI's background tasks for simple cases
        # or FastWorker for more complex distributed processing
        background_tasks.add_task(process_user_registration, user_id, email)

        # Or submit to FastWorker for distributed processing
        # result = await client.delay(
        #     "process_user_registration", user_id, email, priority=TaskPriority.HIGH
        # )

        return {"message": "User registration started", "user_id": user_id}
    else:
        return {"error": "FastWorker client not available"}


@app.post("/send_notification/")
async def send_user_notification(user_id: int, message: str):
    """Send notification to user."""
    if client:
        # Submit to FastWorker with high priority
        result = await client.delay(
            "send_notification", user_id, message, priority=TaskPriority.HIGH
        )
        if result.status == "success":
            return {"message": "Notification sent", "result": result.result}
        else:
            return {"error": result.error}
    else:
        return {"error": "FastWorker client not available"}


@app.post("/process_data/")
async def process_data(data: dict):
    """Process data asynchronously."""
    if client:
        # Submit async task to FastWorker
        result = await client.delay(
            "async_data_processing", data, priority=TaskPriority.NORMAL
        )
        if result.status == "success":
            return {"message": "Data processing completed", "result": result.result}
        else:
            return {"error": result.error}
    else:
        return {"error": "FastWorker client not available"}


@app.post("/process_data_with_callback/")
async def process_data_with_callback(data: dict, callback_address: str):
    """Process data asynchronously with a callback when finished."""
    if client:
        # Submit async task to FastWorker with callback
        result = await client.delay_with_callback(
            "async_data_processing",
            callback_address,
            data,
            priority=TaskPriority.NORMAL,
            callback_data={"endpoint": "/process_data_with_callback/"},
        )
        if result.status == "success":
            return {"message": "Data processing started", "task_id": result.task_id}
        else:
            return {"error": result.error}
    else:
        return {"error": "FastWorker client not available"}


@app.get("/")
async def root():
    """Root endpoint."""
    return {"message": "FastWorker FastAPI Example"}


# To run this example:
# 1. Start one or more FastWorker workers in separate terminals:
#    fastworker worker --worker-id worker1 --task-modules fastworker.examples.tasks
#
# 2. Run this FastAPI application:
#    uvicorn fastworker.examples.fastapi_example:app --reload
#
# 3. Make requests to the endpoints:
#    curl -X POST "http://127.0.0.1:8000/register_user/?user_id=1&email=test@ex.com"
#    curl -X POST "http://127.0.0.1:8000/send_notification/?user_id=1&message=Hello"
#    curl -X POST "http://127.0.0.1:8000/process_data/" \
#      -H "Content-Type: application/json" -d '{"key": "value"}'
#    curl -X POST "http://127.0.0.1:8000/process_data_with_callback/?..." \
#      -H "Content-Type: application/json" -d '{"key": "value"}'

"""Example FastAPI application using FastWorker.

This example demonstrates:
- Zero-boilerplate FastWorker integration with FastWorker(app)
- Non-blocking task submission with delay()
- Blocking submission with submit_task()
- Task callbacks with delay_with_callback()
- Health check using fw.worker_count
- Custom Client configuration via client_kwargs
"""

from fastapi import FastAPI

from fastworker import task
from fastworker.integration.fastapi import FastWorker
from fastworker.tasks.models import TaskPriority

app = FastAPI(title="FastWorker FastAPI Example")
fw = FastWorker(app)  # handles all lifecycle automatically


# -- Task definitions --


@task
def send_welcome_email(user_id: int, email: str) -> str:
    """Send a welcome email."""
    return f"Welcome email sent to user {user_id} at {email}"


@task
def generate_report(report_type: str, params: dict) -> dict:
    """Generate a report."""
    return {"report_type": report_type, "status": "generated", "params": params}


@task
def cleanup_temp_files(directory: str) -> int:
    """Clean up temporary files."""
    return 42  # files deleted


# -- API Endpoints --


@app.post("/users/{user_id}/welcome")
async def welcome_user(user_id: int, email: str):
    """Non-blocking: returns task ID immediately."""
    task_id = await fw.delay("send_welcome_email", user_id, email)
    return {"task_id": task_id, "status": "queued"}


@app.post("/reports/{report_type}")
async def create_report(report_type: str, params: dict):
    """Blocking: waits for the report to finish."""
    result = await fw.submit_task(
        "generate_report", args=(report_type, params),
        priority=TaskPriority.HIGH,
    )
    return {"status": result.status.value, "result": result.result}


@app.post("/tasks/cleanup")
async def trigger_cleanup():
    """With callback: get notified when cleanup completes."""
    task_id = await fw.delay_with_callback(
        "cleanup_temp_files", "tcp://127.0.0.1:6000",
        "/tmp", priority=TaskPriority.LOW,
        callback_data={"notify": "admin"},
    )
    return {"task_id": task_id, "status": "scheduled"}


@app.post("/tasks/batch")
async def batch_submit():
    """Submit multiple tasks atomically."""
    task_ids = await fw.submit_batch([
        {"task_name": "send_welcome_email", "args": (101, "a@b.com")},
        {"task_name": "send_welcome_email", "args": (102, "c@d.com")},
        {"task_name": "cleanup_temp_files", "args": ("/tmp",)},
    ])
    return {"task_ids": task_ids, "count": len(task_ids)}


@app.get("/tasks/{task_id}")
async def task_status(task_id: str):
    """Query task result/status."""
    result = await fw.get_task_result(task_id)
    if result:
        return {"task_id": task_id, "status": result.status.value, "result": result.result}
    local = fw.get_result(task_id)
    if local:
        return {"task_id": task_id, "status": local.status.value, "local": True}
    return {"task_id": task_id, "status": "not_found"}


@app.delete("/tasks/{task_id}")
async def cancel_task(task_id: str):
    """Cancel a queued or running task."""
    cancelled = await fw.cancel_task(task_id)
    return {"task_id": task_id, "cancelled": cancelled}


@app.get("/health")
async def health():
    """Health check including worker discovery status."""
    return {
        "status": "healthy",
        "workers_discovered": fw.worker_count,
    }


@app.get("/")
async def root():
    return {"message": "FastWorker + FastAPI — Zero Broker. Pure Python."}


# To run:
#   Terminal 1: fastworker control-plane --task-modules fastworker.examples.fastapi_example
#   Terminal 2: uvicorn fastworker.examples.fastapi_example:app --reload
#
#   curl -X POST "http://127.0.0.1:8000/users/42/welcome?email=hi@example.com"
#   curl -X POST "http://127.0.0.1:8000/reports/sales" -H "Content-Type: application/json" -d '{"period":"Q1"}'
#   curl http://127.0.0.1:8000/health

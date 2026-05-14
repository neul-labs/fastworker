"""Background tasks — triggered by application events."""

from fastworker import task
from fastworker.examples.level3_organized.app.services.notifications import (
    send_email,
    send_slack,
)


@task
def notify_user(user_id: int, message: str, channels: list[str] = None):
    """Send notification through configured channels."""
    channels = channels or ["email"]
    results = {}
    if "email" in channels:
        results["email"] = send_email(user_id, message)
    if "slack" in channels:
        results["slack"] = send_slack(user_id, message)
    return results


@task
def process_upload(file_path: str, user_id: int):
    """Process an uploaded file."""
    return {"file": file_path, "user": user_id, "status": "processed"}

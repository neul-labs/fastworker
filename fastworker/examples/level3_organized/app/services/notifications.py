"""Service layer — business logic that tasks delegate to."""


def send_email(user_id: int, message: str) -> dict:
    return {"sent": True, "channel": "email", "user_id": user_id}


def send_slack(user_id: int, message: str) -> dict:
    return {"sent": True, "channel": "slack", "user_id": user_id}

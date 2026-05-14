"""Email-related tasks."""

from fastworker import task


@task
def send_welcome_email(user_id: int, email: str) -> str:
    return f"Welcome email sent to user {user_id} at {email}"


@task
def send_password_reset(user_id: int, email: str) -> str:
    return f"Password reset email sent to {email}"

"""Report generation tasks."""

from fastworker import task


@task
def generate_daily_report(date: str) -> dict:
    return {"report": "daily", "date": date, "status": "generated"}


@task
def generate_invoice(invoice_id: int) -> dict:
    return {"invoice_id": invoice_id, "status": "generated"}

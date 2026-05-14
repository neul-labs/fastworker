"""Scheduled tasks — periodic and cron-based background jobs."""

from fastworker import task


@task(repeat_interval=300)
def refresh_cache():
    """Refresh application cache every 5 minutes."""
    return {"cache": "refreshed"}


@task(cron="0 */6 * * *")
def generate_hourly_metrics():
    """Generate metrics report every 6 hours."""
    return {"metrics": "generated"}


@task(cron="0 3 * * *")
def nightly_cleanup():
    """Clean up stale data at 3 AM daily."""
    return {"cleaned": 42}

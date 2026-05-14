"""Schedule configuration for periodic and cron tasks."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Optional


@dataclass
class ScheduleConfig:
    """Configuration for periodic/recurring task execution."""

    repeat_interval: Optional[float] = None  # seconds between executions
    cron_expression: Optional[str] = None  # 5-field cron: "min hour dom month dow"
    repeat_count: Optional[int] = None  # max number of executions (None = unlimited)
    repeat_until: Optional[datetime] = None  # stop repeating after this time

    def __post_init__(self):
        if self.repeat_interval is not None and self.repeat_interval <= 0:
            raise ValueError("repeat_interval must be positive")
        if self.cron_expression and self.repeat_interval:
            raise ValueError("Cannot specify both cron_expression and repeat_interval")
        if not self.cron_expression and not self.repeat_interval:
            raise ValueError("Must specify either cron_expression or repeat_interval")


def _parse_cron_field(field: str, min_val: int, max_val: int) -> set[int]:
    """Parse a single cron field into a set of matching values."""
    if field == "*":
        return set(range(min_val, max_val + 1))

    values: set[int] = set()
    for part in field.split(","):
        step = 1
        if "/" in part:
            part, step_str = part.split("/")
            step = int(step_str)

        if part == "*":
            values.update(range(min_val, max_val + 1, step))
        elif "-" in part:
            lo, hi = part.split("-")
            values.update(range(int(lo), int(hi) + 1, step))
        else:
            values.add(int(part))

    return {v for v in values if min_val <= v <= max_val}


def cron_next(expression: str, from_time: datetime) -> Optional[datetime]:
    """Compute the next fire time for a 5-field cron expression.

    Args:
        expression: 5-field cron string: "minute hour day-of-month month day-of-week"
        from_time: The reference time to compute from.

    Returns:
        The next datetime the expression matches, or None if no match found.
    """
    fields = expression.strip().split()
    if len(fields) != 5:
        raise ValueError(f"Cron expression must have 5 fields, got {len(fields)}")

    minute_field, hour_field, dom_field, month_field, dow_field = fields

    minutes = _parse_cron_field(minute_field, 0, 59)
    hours = _parse_cron_field(hour_field, 0, 23)
    days_of_month = _parse_cron_field(dom_field, 1, 31)
    months = _parse_cron_field(month_field, 1, 12)
    days_of_week = _parse_cron_field(dow_field, 0, 6)

    # Start from the next minute
    candidate = from_time.replace(second=0, microsecond=0) + timedelta(minutes=1)

    # Search up to 2 years ahead to find a match
    end = from_time + timedelta(days=730)
    while candidate <= end:
        if (
            candidate.month in months
            and candidate.day in days_of_month
            and candidate.hour in hours
            and candidate.minute in minutes
            and candidate.weekday() in days_of_week
        ):
            return candidate

        candidate += timedelta(minutes=1)

    return None


def compute_next_eta(
    config: ScheduleConfig,
    now: datetime,
    times_run: int,
) -> Optional[datetime]:
    """Compute the next ETA for a periodic task.

    Args:
        config: The schedule configuration.
        now: Current time.
        times_run: Number of times this task has already executed.

    Returns:
        Next datetime to run, or None if no more executions needed.
    """
    # Check repeat_count limit
    if config.repeat_count is not None and times_run >= config.repeat_count:
        return None

    if config.cron_expression:
        next_time = cron_next(config.cron_expression, now)
    elif config.repeat_interval:
        next_time = now + timedelta(seconds=config.repeat_interval)
    else:
        return None

    # Check repeat_until limit
    if config.repeat_until and next_time and next_time > config.repeat_until:
        return None

    return next_time

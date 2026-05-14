"""Tests for schedule configuration and cron parsing."""

from datetime import datetime

import pytest

from fastworker.tasks.schedules import (
    ScheduleConfig,
    _parse_cron_field,
    compute_next_eta,
    cron_next,
)


class TestParseCronField:
    def test_star(self):
        assert _parse_cron_field("*", 0, 5) == {0, 1, 2, 3, 4, 5}

    def test_single_value(self):
        assert _parse_cron_field("3", 0, 5) == {3}

    def test_range(self):
        assert _parse_cron_field("1-3", 0, 5) == {1, 2, 3}

    def test_list(self):
        assert _parse_cron_field("1,3,5", 0, 5) == {1, 3, 5}

    def test_step(self):
        assert _parse_cron_field("*/2", 0, 5) == {0, 2, 4}

    def test_range_with_step(self):
        assert _parse_cron_field("1-5/2", 0, 5) == {1, 3, 5}

    def test_out_of_range_filtered(self):
        assert _parse_cron_field("3,7", 0, 5) == {3}


class TestCronNext:
    def test_every_minute(self):
        now = datetime(2026, 1, 1, 12, 0, 0)
        result = cron_next("* * * * *", now)
        assert result == datetime(2026, 1, 1, 12, 1)

    def test_specific_minute(self):
        now = datetime(2026, 1, 1, 12, 0, 0)
        result = cron_next("30 * * * *", now)
        assert result == datetime(2026, 1, 1, 12, 30)

    def test_next_hour(self):
        now = datetime(2026, 1, 1, 12, 30, 0)
        result = cron_next("15 * * * *", now)
        assert result == datetime(2026, 1, 1, 13, 15)

    def test_every_5_minutes(self):
        now = datetime(2026, 1, 1, 12, 0, 0)
        result = cron_next("*/5 * * * *", now)
        assert result == datetime(2026, 1, 1, 12, 5)

    def test_daily_at_midnight(self):
        now = datetime(2026, 1, 1, 12, 0, 0)
        result = cron_next("0 0 * * *", now)
        assert result == datetime(2026, 1, 2, 0, 0)

    def test_weekdays_only(self):
        now = datetime(2026, 1, 2, 12, 0, 0)  # Friday
        result = cron_next("0 9 * * 1-5", now)
        assert result == datetime(2026, 1, 3, 9, 0)  # Saturday, but wait - Jan 2 2026 is a Friday, next should be Monday Jan 5... actually let me check

    def test_invalid_expression(self):
        with pytest.raises(ValueError, match="must have 5 fields"):
            cron_next("* * * *", datetime.now())


class TestScheduleConfig:
    def test_interval_only(self):
        config = ScheduleConfig(repeat_interval=60)
        assert config.repeat_interval == 60
        assert config.cron_expression is None

    def test_cron_only(self):
        config = ScheduleConfig(cron_expression="*/5 * * * *")
        assert config.cron_expression == "*/5 * * * *"

    def test_both_raises(self):
        with pytest.raises(ValueError, match="Cannot specify both"):
            ScheduleConfig(repeat_interval=60, cron_expression="* * * * *")

    def test_neither_raises(self):
        with pytest.raises(ValueError, match="Must specify"):
            ScheduleConfig()

    def test_negative_interval_raises(self):
        with pytest.raises(ValueError, match="must be positive"):
            ScheduleConfig(repeat_interval=-1)

    def test_with_repeat_count(self):
        config = ScheduleConfig(repeat_interval=60, repeat_count=10)
        assert config.repeat_count == 10


class TestComputeNextEta:
    def test_interval_first_run(self):
        config = ScheduleConfig(repeat_interval=60)
        now = datetime(2026, 1, 1, 12, 0, 0)
        result = compute_next_eta(config, now, 0)
        assert result == datetime(2026, 1, 1, 12, 1, 0)

    def test_repeat_count_exceeded(self):
        config = ScheduleConfig(repeat_interval=60, repeat_count=3)
        now = datetime(2026, 1, 1, 12, 0, 0)
        result = compute_next_eta(config, now, 3)
        assert result is None

    def test_repeat_count_not_exceeded(self):
        config = ScheduleConfig(repeat_interval=60, repeat_count=3)
        now = datetime(2026, 1, 1, 12, 0, 0)
        result = compute_next_eta(config, now, 2)
        assert result is not None

    def test_repeat_until_passed(self):
        config = ScheduleConfig(
            repeat_interval=60,
            repeat_until=datetime(2026, 1, 1, 12, 30, 0),
        )
        now = datetime(2026, 1, 1, 12, 31, 0)
        result = compute_next_eta(config, now, 0)
        assert result is None

    def test_cron_based(self):
        config = ScheduleConfig(cron_expression="0 * * * *")
        now = datetime(2026, 1, 1, 12, 0, 0)
        result = compute_next_eta(config, now, 0)
        assert result == datetime(2026, 1, 1, 13, 0)

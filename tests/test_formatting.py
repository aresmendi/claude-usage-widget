import datetime

from widget.formatting import bar_color_for_pct, format_time_ago, format_time_remaining

_NOW = datetime.datetime(2026, 7, 2, 10, 0, 0, tzinfo=datetime.timezone.utc)


def test_empty_input_returns_dash():
    assert format_time_remaining("") == "—"


def test_invalid_iso_returns_dash():
    assert format_time_remaining("no-es-una-fecha", now=_NOW) == "—"


def test_hours_minutes_seconds():
    reset_at = "2026-07-02T13:12:05+00:00"
    assert format_time_remaining(reset_at, now=_NOW) == "3h 12min 5s"


def test_minutes_seconds_no_hours():
    reset_at = "2026-07-02T10:05:30+00:00"
    assert format_time_remaining(reset_at, now=_NOW) == "5min 30s"


def test_seconds_only():
    reset_at = "2026-07-02T10:00:45+00:00"
    assert format_time_remaining(reset_at, now=_NOW) == "45s"


def test_past_reset_shows_restarting():
    reset_at = "2026-07-02T09:00:00+00:00"
    assert format_time_remaining(reset_at, now=_NOW) == "reiniciando…"


def test_naive_iso_treated_as_utc():
    reset_at = "2026-07-02T11:00:00"
    assert format_time_remaining(reset_at, now=_NOW) == "1h 0min 0s"


def test_days_hours_minutes_for_long_durations():
    reset_at = "2026-07-08T08:00:00+00:00"
    assert format_time_remaining(reset_at, now=_NOW) == "5d 22h 0min"


def test_time_ago_empty_input_returns_dash():
    assert format_time_ago("") == "—"


def test_time_ago_invalid_iso_returns_dash():
    assert format_time_ago("no-es-una-fecha", now=_NOW) == "—"


def test_time_ago_just_now():
    then = "2026-07-02T09:59:58+00:00"
    assert format_time_ago(then, now=_NOW) == "justo ahora"


def test_time_ago_minutes():
    then = "2026-07-02T09:55:00+00:00"
    assert format_time_ago(then, now=_NOW) == "hace 5min"


def test_time_ago_hours_minutes():
    then = "2026-07-02T07:30:00+00:00"
    assert format_time_ago(then, now=_NOW) == "hace 2h 30min"


def test_time_ago_days_hours():
    then = "2026-06-30T04:00:00+00:00"
    assert format_time_ago(then, now=_NOW) == "hace 2d 6h"


def test_time_ago_seconds_only():
    then = "2026-07-02T09:59:40+00:00"
    assert format_time_ago(then, now=_NOW) == "hace 20s"


def test_bar_color_normal_below_90():
    assert bar_color_for_pct(50.0) == "#2fa84f"


def test_bar_color_near_limit_at_90():
    assert bar_color_for_pct(90.0) == "#e08a2e"


def test_bar_color_near_limit_below_100():
    assert bar_color_for_pct(99.9) == "#e08a2e"


def test_bar_color_at_limit_100_or_more():
    assert bar_color_for_pct(100.0) == "#d94f4f"
    assert bar_color_for_pct(150.0) == "#d94f4f"

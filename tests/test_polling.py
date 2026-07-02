import threading
from contextlib import ExitStack
from unittest.mock import MagicMock, patch

import pytest

from widget.config import Config
from widget.cookie_reader import CookieError
from widget.fetcher import AuthError, FetchError, UsageData
from widget.polling import polling_loop

_CFG = Config(browser="firefox", alert_threshold=70.0, weekly_expanded=False)


def _ok(pct=50.0, reset_at="2026-07-01T18:00:00Z", wpct=20.0, wreset="2026-07-07T00:00:00Z"):
    return UsageData(
        five_hour_pct=pct,
        five_hour_reset_at=reset_at,
        seven_day_pct=wpct,
        seven_day_reset_at=wreset,
    )


def _run(ticks: int, fetch_seq):
    """Ejecuta polling_loop por N ticks. Devuelve (estados, notify_calls, mocks)."""
    states = []
    notify_calls = []
    stop = threading.Event()
    mock_key = MagicMock(return_value="session-key")
    mock_resolve = MagicMock(return_value="org-1")
    mock_fetch = MagicMock(side_effect=list(fetch_seq))
    mock_notify = MagicMock(side_effect=lambda t, m: notify_calls.append(m))

    def dispatch(s):
        states.append(s)
        if len(states) >= ticks:
            stop.set()

    with ExitStack() as stack:
        stack.enter_context(patch("widget.cookie_reader.get_session_key", mock_key))
        stack.enter_context(patch("widget.fetcher.resolve_org_id", mock_resolve))
        stack.enter_context(patch("widget.fetcher.fetch_usage", mock_fetch))
        stack.enter_context(patch("widget.notifier.notify", mock_notify))
        polling_loop(_CFG, stop, dispatch, interval=0)

    return states, notify_calls, {"key": mock_key, "resolve": mock_resolve}


# ── State transitions ──────────────────────────────────────────────────────


class TestStateTransitions:

    def test_ok_on_success(self):
        states, _, _ = _run(1, [_ok(pct=30.0)])
        assert states[0].session_status == "ok"
        assert states[0].five_hour_pct == 30.0

    def test_expired_on_auth_error(self):
        states, _, _ = _run(1, [AuthError("401")])
        assert states[0].session_status == "expired"

    def test_error_on_fetch_error(self):
        states, _, _ = _run(1, [FetchError("timeout")])
        assert states[0].session_status == "error"
        assert "timeout" in states[0].error_message

    def test_error_on_cookie_error(self):
        states = []
        stop = threading.Event()

        def dispatch(s):
            states.append(s)
            stop.set()

        with patch("widget.cookie_reader.get_session_key", side_effect=CookieError("no cookie")):
            with patch("widget.fetcher.resolve_org_id", return_value="org-1"):
                with patch("widget.fetcher.fetch_usage"):
                    with patch("widget.notifier.notify"):
                        polling_loop(_CFG, stop, dispatch, interval=0)

        assert states[0].session_status == "error"
        assert "no cookie" in states[0].error_message

    def test_ok_expired_ok_sequence(self):
        states, _, _ = _run(3, [_ok(), AuthError("403"), _ok()])
        assert [s.session_status for s in states] == ["ok", "expired", "ok"]

    def test_ok_error_ok_sequence(self):
        states, _, _ = _run(3, [_ok(), FetchError("net"), _ok()])
        assert [s.session_status for s in states] == ["ok", "error", "ok"]

    def test_data_fields_propagated_on_ok(self):
        states, _, _ = _run(1, [_ok(pct=42.0, reset_at="2026-07-01T20:00:00Z")])
        s = states[0]
        assert s.five_hour_pct == 42.0
        assert s.five_hour_reset_at == "2026-07-01T20:00:00Z"


# ── Alert deduplication ───────────────────────────────────────────────────


class TestAlertDedup:

    def test_notify_fired_when_threshold_exceeded(self):
        _, calls, _ = _run(1, [_ok(pct=71.0)])
        assert len(calls) == 1

    def test_no_notify_below_threshold(self):
        _, calls, _ = _run(2, [_ok(pct=50.0), _ok(pct=65.0)])
        assert len(calls) == 0

    def test_no_repeat_notify_same_reset_window(self):
        reset = "2026-07-01T18:00:00Z"
        _, calls, _ = _run(3, [
            _ok(pct=71.0, reset_at=reset),  # → notify
            _ok(pct=75.0, reset_at=reset),  # → no notify (mismo window)
            _ok(pct=80.0, reset_at=reset),  # → no notify
        ])
        assert len(calls) == 1

    def test_re_trigger_after_drop_below_threshold(self):
        reset = "2026-07-01T18:00:00Z"
        _, calls, _ = _run(3, [
            _ok(pct=71.0, reset_at=reset),  # → notify; alerted_for = reset
            _ok(pct=50.0, reset_at=reset),  # → drop below → alerted_for = None
            _ok(pct=72.0, reset_at=reset),  # → notify de nuevo
        ])
        assert len(calls) == 2

    def test_new_reset_window_triggers_new_notify(self):
        _, calls, _ = _run(2, [
            _ok(pct=71.0, reset_at="2026-07-01T18:00:00Z"),  # → notify; alerted_for = "18:00"
            _ok(pct=71.0, reset_at="2026-07-01T23:00:00Z"),  # → nuevo window → notify
        ])
        assert len(calls) == 2


# ── org_id / session_key caching ──────────────────────────────────────────


class TestCaching:

    def test_org_id_resolved_once_on_repeated_success(self):
        _, _, mocks = _run(3, [_ok(), _ok(), _ok()])
        assert mocks["resolve"].call_count == 1

    def test_session_key_fetched_once_on_repeated_success(self):
        _, _, mocks = _run(3, [_ok(), _ok(), _ok()])
        assert mocks["key"].call_count == 1

    def test_org_id_re_resolved_after_auth_error(self):
        _, _, mocks = _run(3, [_ok(), AuthError("401"), _ok()])
        # tick 1: resolve. tick 2: AuthError → reset. tick 3: resolve de nuevo.
        assert mocks["resolve"].call_count == 2

    def test_session_key_re_fetched_after_auth_error(self):
        _, _, mocks = _run(3, [_ok(), AuthError("401"), _ok()])
        assert mocks["key"].call_count == 2

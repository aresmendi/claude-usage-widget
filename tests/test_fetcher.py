import logging
from unittest.mock import MagicMock, patch

import pytest
import requests as req_lib

from widget.fetcher import (
    AuthError,
    FetchError,
    UsageData,
    fetch_usage,
    resolve_org_id,
)


def _resp(status: int, body=None) -> MagicMock:
    m = MagicMock()
    m.status_code = status
    m.ok = 200 <= status < 400
    if body is not None:
        m.json.return_value = body
    return m


# ── resolve_org_id ─────────────────────────────────────────────────────────


class TestResolveOrgId:
    PATCH = "widget.fetcher.requests.get"

    def test_list_response_returns_id(self):
        with patch(self.PATCH, return_value=_resp(200, [{"id": "org-abc"}])):
            assert resolve_org_id("key") == "org-abc"

    def test_dict_response_returns_id(self):
        with patch(self.PATCH, return_value=_resp(200, {"id": "org-xyz"})):
            assert resolve_org_id("key") == "org-xyz"

    def test_uuid_field_fallback(self):
        with patch(self.PATCH, return_value=_resp(200, [{"uuid": "org-uuid"}])):
            assert resolve_org_id("key") == "org-uuid"

    def test_401_raises_auth_error(self):
        with patch(self.PATCH, return_value=_resp(401)):
            with pytest.raises(AuthError):
                resolve_org_id("key")

    def test_403_raises_auth_error(self):
        with patch(self.PATCH, return_value=_resp(403)):
            with pytest.raises(AuthError):
                resolve_org_id("key")

    def test_500_raises_fetch_error(self):
        with patch(self.PATCH, return_value=_resp(500)):
            with pytest.raises(FetchError, match="500"):
                resolve_org_id("key")

    def test_timeout_raises_fetch_error(self):
        with patch(self.PATCH, side_effect=req_lib.exceptions.Timeout()):
            with pytest.raises(FetchError, match="timeout"):
                resolve_org_id("key")

    def test_network_error_raises_fetch_error(self):
        with patch(self.PATCH, side_effect=req_lib.exceptions.ConnectionError("err")):
            with pytest.raises(FetchError, match="network error"):
                resolve_org_id("key")

    def test_empty_list_raises_fetch_error(self):
        with patch(self.PATCH, return_value=_resp(200, [])):
            with pytest.raises(FetchError):
                resolve_org_id("key")

    def test_unexpected_shape_logs_warning(self, caplog):
        with caplog.at_level(logging.WARNING, logger="widget.fetcher"):
            with patch(self.PATCH, return_value=_resp(200, [])):
                with pytest.raises(FetchError):
                    resolve_org_id("key")
        assert any("inesperado" in r.message.lower() for r in caplog.records)

    def test_session_key_sent_as_cookie(self):
        with patch(self.PATCH, return_value=_resp(200, [{"id": "org-1"}])) as mock_get:
            resolve_org_id("my-session")
        _, kwargs = mock_get.call_args
        assert "my-session" in kwargs["headers"]["Cookie"]


# ── fetch_usage ────────────────────────────────────────────────────────────


class TestFetchUsage:
    PATCH = "widget.fetcher.requests.get"

    FULL = {
        "five_hour": {
            "utilization": 71.5,
            "resets_at": "2026-07-01T18:00:00Z",
        },
        "seven_day": {
            "utilization": 25.0,
            "resets_at": "2026-07-07T00:00:00Z",
        },
    }

    def test_happy_path(self):
        with patch(self.PATCH, return_value=_resp(200, self.FULL)):
            d = fetch_usage("key", "org-1")
        assert isinstance(d, UsageData)
        assert d.five_hour_pct == 71.5
        assert d.five_hour_reset_at == "2026-07-01T18:00:00Z"
        assert d.seven_day_pct == 25.0
        assert d.seven_day_reset_at == "2026-07-07T00:00:00Z"

    def test_missing_fields_returns_defaults_no_crash(self, caplog):
        with caplog.at_level(logging.WARNING, logger="widget.fetcher"):
            with patch(self.PATCH, return_value=_resp(200, {})):
                d = fetch_usage("key", "org-1")
        assert d.five_hour_pct == 0.0
        assert d.five_hour_reset_at == ""
        assert d.seven_day_pct == 0.0
        assert d.seven_day_reset_at == ""
        assert caplog.records

    def test_non_numeric_pct_returns_zero_and_logs(self, caplog):
        body = {
            "five_hour": {"utilization": "N/A"},
            "seven_day": {"utilization": "N/A"},
        }
        with caplog.at_level(logging.WARNING, logger="widget.fetcher"):
            with patch(self.PATCH, return_value=_resp(200, body)):
                d = fetch_usage("key", "org-1")
        assert d.five_hour_pct == 0.0
        assert d.seven_day_pct == 0.0

    def test_non_dict_body_does_not_crash(self, caplog):
        with caplog.at_level(logging.WARNING, logger="widget.fetcher"):
            with patch(self.PATCH, return_value=_resp(200, [1, 2, 3])):
                d = fetch_usage("key", "org-1")
        assert d.five_hour_pct == 0.0
        assert any("inesperado" in r.message.lower() for r in caplog.records)

    def test_401_raises_auth_error(self):
        with patch(self.PATCH, return_value=_resp(401)):
            with pytest.raises(AuthError):
                fetch_usage("key", "org-1")

    def test_403_raises_auth_error(self):
        with patch(self.PATCH, return_value=_resp(403)):
            with pytest.raises(AuthError):
                fetch_usage("key", "org-1")

    def test_500_raises_fetch_error(self):
        with patch(self.PATCH, return_value=_resp(500)):
            with pytest.raises(FetchError, match="500"):
                fetch_usage("key", "org-1")

    def test_timeout_raises_fetch_error(self):
        with patch(self.PATCH, side_effect=req_lib.exceptions.Timeout()):
            with pytest.raises(FetchError, match="timeout"):
                fetch_usage("key", "org-1")

    def test_network_error_raises_fetch_error(self):
        with patch(self.PATCH, side_effect=req_lib.exceptions.ConnectionError("ko")):
            with pytest.raises(FetchError, match="network error"):
                fetch_usage("key", "org-1")

    def test_org_id_included_in_url(self):
        with patch(self.PATCH, return_value=_resp(200, {})) as mock_get:
            fetch_usage("key", "org-specific")
        url = mock_get.call_args[0][0]
        assert "org-specific" in url

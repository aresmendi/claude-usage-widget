import logging
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

import pytest

from widget.cookie_reader import CookieError, get_session_key

# Cookies de prueba usando SimpleNamespace para evitar colisiones con MagicMock.name
_SESSION = SimpleNamespace(name="sessionKey", domain="claude.ai", value="sk-test-token")
_OTHER = SimpleNamespace(name="csrftoken", domain="claude.ai", value="x")
_WRONG_DOMAIN = SimpleNamespace(name="sessionKey", domain="other.com", value="y")

_BROWSERS = "widget.cookie_reader.SUPPORTED_BROWSERS"
_SLEEP = "widget.cookie_reader.time.sleep"


class TestGetSessionKey:

    def test_firefox_finds_session_cookie(self):
        mock_fn = MagicMock(return_value=[_SESSION])
        with patch(_BROWSERS, {"firefox": mock_fn}):
            assert get_session_key("firefox") == "sk-test-token"
        mock_fn.assert_called_once_with(domain_name="claude.ai")

    def test_chrome_finds_session_cookie(self):
        mock_fn = MagicMock(return_value=[_SESSION])
        with patch(_BROWSERS, {"chrome": mock_fn}):
            assert get_session_key("chrome") == "sk-test-token"

    def test_returns_first_matching_cookie(self):
        mock_fn = MagicMock(return_value=[_OTHER, _SESSION])
        with patch(_BROWSERS, {"firefox": mock_fn}):
            assert get_session_key("firefox") == "sk-test-token"

    def test_wrong_domain_cookie_ignored(self):
        mock_fn = MagicMock(return_value=[_WRONG_DOMAIN])
        with patch(_BROWSERS, {"firefox": mock_fn}):
            with pytest.raises(CookieError, match="sessionKey"):
                get_session_key("firefox")

    def test_unsupported_browser_raises_cookie_error(self):
        with patch(_BROWSERS, {"firefox": MagicMock()}):
            with pytest.raises(CookieError, match="soportado"):
                get_session_key("safari")

    def test_cookie_absent_raises_cookie_error(self):
        mock_fn = MagicMock(return_value=[_OTHER])
        with patch(_BROWSERS, {"firefox": mock_fn}):
            with pytest.raises(CookieError, match="sessionKey"):
                get_session_key("firefox")

    def test_empty_jar_raises_cookie_error(self):
        mock_fn = MagicMock(return_value=[])
        with patch(_BROWSERS, {"firefox": mock_fn}):
            with pytest.raises(CookieError):
                get_session_key("firefox")

    def test_firefox_sqlite_locked_retries_once(self):
        exc = Exception("database is locked")
        mock_fn = MagicMock(side_effect=[exc, [_SESSION]])
        with patch(_BROWSERS, {"firefox": mock_fn}):
            with patch(_SLEEP) as mock_sleep:
                result = get_session_key("firefox")
        assert result == "sk-test-token"
        mock_sleep.assert_called_once_with(2)
        assert mock_fn.call_count == 2

    def test_firefox_retry_also_fails_raises_cookie_error(self):
        exc = Exception("database is locked")
        mock_fn = MagicMock(side_effect=[exc, exc])
        with patch(_BROWSERS, {"firefox": mock_fn}):
            with patch(_SLEEP):
                with pytest.raises(CookieError, match="reintento"):
                    get_session_key("firefox")
        assert mock_fn.call_count == 2

    def test_firefox_first_failure_logs_warning(self, caplog):
        exc = Exception("locked")
        mock_fn = MagicMock(side_effect=[exc, [_SESSION]])
        with caplog.at_level(logging.WARNING, logger="widget.cookie_reader"):
            with patch(_BROWSERS, {"firefox": mock_fn}):
                with patch(_SLEEP):
                    get_session_key("firefox")
        assert caplog.records

    def test_non_firefox_error_raises_immediately_no_retry(self):
        mock_fn = MagicMock(side_effect=Exception("io error"))
        with patch(_BROWSERS, {"chrome": mock_fn}):
            with pytest.raises(CookieError):
                get_session_key("chrome")
        assert mock_fn.call_count == 1

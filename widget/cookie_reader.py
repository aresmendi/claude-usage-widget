import logging
import time

logger = logging.getLogger(__name__)

_DOMAIN = "claude.ai"
_KEY = "sessionKey"

try:
    import browser_cookie3 as _bc3

    # Solo Firefox: Chrome y los navegadores basados en Chromium (Opera,
    # Opera GX) cifran las cookies en Windows con "App-Bound Encryption"
    # desde mediados de 2024, que browser_cookie3 no puede descifrar sin
    # recurrir a las mismas técnicas que usa el malware de robo de cookies.
    # Firefox guarda las cookies en SQLite sin cifrar y no tiene ese problema.
    SUPPORTED_BROWSERS: dict[str, callable] = {
        "firefox": _bc3.firefox,
    }
except ImportError:
    # browser_cookie3 no instalado; SUPPORTED_BROWSERS vacío hasta que esté disponible
    SUPPORTED_BROWSERS: dict[str, callable] = {}


class CookieError(Exception):
    """Error al extraer la cookie de sesión del navegador."""


def get_session_key(browser: str) -> str:
    """Extrae sessionKey de claude.ai del navegador indicado.

    Firefox: reintenta una vez tras 2s si el primer intento falla (SQLite lock).
    """
    if browser not in SUPPORTED_BROWSERS:
        raise CookieError(f"Navegador no soportado: {browser!r}")

    jar = _load_jar(browser, SUPPORTED_BROWSERS[browser])

    for cookie in jar:
        if cookie.name == _KEY and _DOMAIN in (cookie.domain or ""):
            return cookie.value

    raise CookieError(f"Cookie {_KEY!r} no encontrada para {_DOMAIN!r} en {browser!r}")


def _load_jar(browser: str, fn: callable):
    """Carga el jar de cookies; Firefox reintenta una vez en caso de error."""
    try:
        return fn(domain_name=_DOMAIN)
    except Exception as exc:
        if browser != "firefox":
            raise CookieError(f"Error leyendo cookies de {browser!r}: {exc}") from exc
        logger.warning(
            "cookie_reader: primer intento fallido en firefox (%s); reintentando en 2s", exc
        )

    time.sleep(2)

    try:
        return fn(domain_name=_DOMAIN)
    except Exception as exc:
        raise CookieError(f"Error leyendo cookies de firefox tras reintento: {exc}") from exc

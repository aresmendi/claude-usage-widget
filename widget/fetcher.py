import logging

import requests
from dataclasses import dataclass

logger = logging.getLogger(__name__)

_BASE = "https://claude.ai/api"


@dataclass(frozen=True)
class UsageData:
    five_hour_pct: float
    five_hour_reset_at: str  # ISO8601 o ""
    seven_day_pct: float
    seven_day_reset_at: str  # ISO8601 o ""


class AuthError(Exception):
    """401/403 — sesión caducada."""


class FetchError(Exception):
    """Error de red, timeout o shape inesperado."""


def _headers(session_key: str) -> dict[str, str]:
    # Cloudflare bloquea peticiones con User-Agent/headers no-navegador
    # (devuelve un reto JS con 403). Hace falta imitar un navegador real.
    return {
        "Cookie": f"sessionKey={session_key}",
        "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36",
        "Accept": "application/json, text/plain, */*",
        "Accept-Language": "es-ES,es;q=0.9,en;q=0.8",
        "Referer": "https://claude.ai/",
        "anthropic-client-version": "0",
        "x-requested-with": "XMLHttpRequest",
    }


def resolve_org_id(session_key: str) -> str:
    """GET /api/organizations — devuelve el primer org_id."""
    try:
        resp = requests.get(
            f"{_BASE}/organizations",
            headers=_headers(session_key),
            timeout=10,
        )
    except requests.exceptions.Timeout:
        raise FetchError("resolve_org_id: timeout")
    except requests.exceptions.RequestException as exc:
        raise FetchError(f"resolve_org_id: network error — {exc}") from exc

    if resp.status_code in (401, 403):
        raise AuthError(f"resolve_org_id: HTTP {resp.status_code}")
    if not resp.ok:
        raise FetchError(f"resolve_org_id: HTTP {resp.status_code}")

    try:
        payload = resp.json()
    except ValueError as exc:
        raise FetchError(f"resolve_org_id: JSON inválido — {exc}") from exc

    org_id = _extract_org_id(payload)
    if not org_id:
        logger.warning("resolve_org_id: shape inesperado — %r", payload)
        raise FetchError("resolve_org_id: no se pudo extraer org_id")
    return org_id


def _extract_org_id(payload: object) -> str | None:
    if isinstance(payload, list) and payload:
        entry = payload[0]
    elif isinstance(payload, dict):
        entry = payload
    else:
        return None
    raw = entry.get("uuid") or entry.get("id") or ""  # la API requiere UUID, no id numérico
    return str(raw) if raw else None


def fetch_usage(session_key: str, org_id: str) -> UsageData:
    """GET /api/organizations/{org_id}/usage — porcentajes de uso.

    Parsing tolerante: campos ausentes retornan 0/'' y emiten warning.
    NOTE: nombres de campo pendientes de verificar contra respuesta real.
    """
    try:
        resp = requests.get(
            f"{_BASE}/organizations/{org_id}/usage",
            headers=_headers(session_key),
            timeout=10,
        )
    except requests.exceptions.Timeout:
        raise FetchError("fetch_usage: timeout")
    except requests.exceptions.RequestException as exc:
        raise FetchError(f"fetch_usage: network error — {exc}") from exc

    if resp.status_code in (401, 403):
        raise AuthError(f"fetch_usage: HTTP {resp.status_code}")
    if not resp.ok:
        raise FetchError(f"fetch_usage: HTTP {resp.status_code}")

    try:
        data = resp.json()
    except ValueError as exc:
        raise FetchError(f"fetch_usage: JSON inválido — {exc}") from exc

    if not isinstance(data, dict):
        logger.warning("fetch_usage: shape inesperado — %r", type(data).__name__)
        data = {}

    five_hour = data.get("five_hour") or {}
    seven_day = data.get("seven_day") or {}

    if not isinstance(five_hour, dict):
        logger.warning("fetch_usage: five_hour no es dict — %r", type(five_hour).__name__)
        five_hour = {}
    if not isinstance(seven_day, dict):
        logger.warning("fetch_usage: seven_day no es dict — %r", type(seven_day).__name__)
        seven_day = {}

    return UsageData(
        five_hour_pct=_safe_float(five_hour, "utilization"),
        five_hour_reset_at=_safe_str(five_hour, "resets_at"),
        seven_day_pct=_safe_float(seven_day, "utilization"),
        seven_day_reset_at=_safe_str(seven_day, "resets_at"),
    )


def _safe_float(data: dict, key: str) -> float:
    val = data.get(key)
    if val is None:
        logger.warning("fetch_usage: campo ausente %r", key)
        return 0.0
    try:
        return float(val)
    except (TypeError, ValueError):
        logger.warning("fetch_usage: valor no numérico en %r: %r", key, val)
        return 0.0


def _safe_str(data: dict, key: str) -> str:
    val = data.get(key)
    if val is None:
        logger.warning("fetch_usage: campo ausente %r", key)
        return ""
    return str(val)

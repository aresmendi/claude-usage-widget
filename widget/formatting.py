from __future__ import annotations

import datetime


def format_time_remaining(reset_at_iso: str, *, now: datetime.datetime | None = None) -> str:
    """Convierte un timestamp ISO8601 futuro en el tiempo restante, p.ej. '3h 12min 5s'.

    Devuelve '—' si `reset_at_iso` está vacío o no es un ISO8601 válido.
    """
    if not reset_at_iso:
        return "—"
    try:
        reset_at = datetime.datetime.fromisoformat(reset_at_iso)
    except ValueError:
        return "—"

    now = now or datetime.datetime.now(tz=datetime.timezone.utc)
    if reset_at.tzinfo is None:
        reset_at = reset_at.replace(tzinfo=datetime.timezone.utc)

    total_seconds = int((reset_at - now).total_seconds())
    if total_seconds <= 0:
        return "reiniciando…"

    days, remainder = divmod(total_seconds, 86400)
    hours, remainder = divmod(remainder, 3600)
    minutes, seconds = divmod(remainder, 60)

    if days:
        return f"{days}d {hours}h {minutes}min"
    if hours:
        return f"{hours}h {minutes}min {seconds}s"
    if minutes:
        return f"{minutes}min {seconds}s"
    return f"{seconds}s"


def format_time_ago(iso: str, *, now: datetime.datetime | None = None) -> str:
    """Convierte un timestamp ISO8601 pasado en 'hace Xh Ymin', p.ej. 'hace 2min'.

    Devuelve '—' si `iso` está vacío o no es un ISO8601 válido.
    """
    if not iso:
        return "—"
    try:
        then = datetime.datetime.fromisoformat(iso)
    except ValueError:
        return "—"

    now = now or datetime.datetime.now(tz=datetime.timezone.utc)
    if then.tzinfo is None:
        then = then.replace(tzinfo=datetime.timezone.utc)

    total_seconds = max(0, int((now - then).total_seconds()))
    if total_seconds < 5:
        return "justo ahora"

    days, remainder = divmod(total_seconds, 86400)
    hours, remainder = divmod(remainder, 3600)
    minutes, seconds = divmod(remainder, 60)

    if days:
        return f"hace {days}d {hours}h"
    if hours:
        return f"hace {hours}h {minutes}min"
    if minutes:
        return f"hace {minutes}min"
    return f"hace {seconds}s"


# Verde = normal, naranja = cerca del límite, rojo = en el límite.
# Mismos umbrales que usa Tokenio (referencia de diseño para macOS).
_COLOR_NORMAL = "#2fa84f"
_COLOR_NEAR_LIMIT = "#e08a2e"
_COLOR_AT_LIMIT = "#d94f4f"


def bar_color_for_pct(pct: float) -> str:
    """Color de la barra de progreso según el porcentaje de uso."""
    if pct >= 100:
        return _COLOR_AT_LIMIT
    if pct >= 90:
        return _COLOR_NEAR_LIMIT
    return _COLOR_NORMAL

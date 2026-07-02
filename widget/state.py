from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class UsageState:
    five_hour_pct: float
    five_hour_reset_at: str   # ISO8601
    seven_day_pct: float
    seven_day_reset_at: str   # ISO8601
    session_status: str       # "ok" | "expired" | "error"
    last_updated: str         # ISO8601
    error_message: str = ""


# Valor inicial antes del primer ciclo de polling.
EMPTY_STATE = UsageState(
    five_hour_pct=0.0,
    five_hour_reset_at="",
    seven_day_pct=0.0,
    seven_day_reset_at="",
    session_status="error",
    last_updated="",
    error_message="No data yet",
)

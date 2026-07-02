import datetime
import logging
import threading
from dataclasses import replace
from typing import Callable

from widget import cookie_reader, fetcher, notifier
from widget.config import Config
from widget.state import EMPTY_STATE, UsageState

logger = logging.getLogger(__name__)


def polling_loop(
    config: Config,
    stop_event: threading.Event,
    dispatch: Callable[[UsageState], None],
    *,
    interval: int = 60,
) -> None:
    """Bucle de polling. Corre en hilo daemon. Nunca eleva excepciones."""
    session_key: str | None = None
    org_id: str | None = None
    # No se usa five_hour_reset_at como clave de dedup: la API no garantiza que
    # sea un timestamp fijo por ventana (puede recalcularse en cada respuesta),
    # así que comparar contra él puede disparar una notificación en cada poll.
    alerted: bool = False

    while not stop_event.is_set():
        state, session_key, org_id, alerted = _poll_once(
            config, session_key, org_id, alerted
        )
        dispatch(state)
        stop_event.wait(interval)


def _poll_once(
    config: Config,
    session_key: str | None,
    org_id: str | None,
    alerted: bool,
) -> tuple[UsageState, str | None, str | None, bool]:
    """Ejecuta un ciclo de fetch + alerta. Nunca eleva excepciones."""
    try:
        session_key = session_key or cookie_reader.get_session_key(config.browser)
        org_id = org_id or fetcher.resolve_org_id(session_key)
        d = fetcher.fetch_usage(session_key, org_id)

        s = UsageState(
            five_hour_pct=d.five_hour_pct,
            five_hour_reset_at=d.five_hour_reset_at,
            seven_day_pct=d.seven_day_pct,
            seven_day_reset_at=d.seven_day_reset_at,
            session_status="ok",
            last_updated=_now(),
        )

        try:
            if d.five_hour_pct >= config.alert_threshold:
                if not alerted:
                    notifier.notify(
                        "Claude usage",
                        f"Uso: {d.five_hour_pct:.0f}% · Reset: {d.five_hour_reset_at}",
                    )
                    alerted = True
            else:
                alerted = False
        except Exception as exc:
            logger.warning("polling: error en notificación — %s", exc)

    except fetcher.AuthError:
        s = _error_state("expired")
        session_key = org_id = None

    except (cookie_reader.CookieError, fetcher.FetchError) as exc:
        s = _error_state("error", str(exc))
        org_id = None

    except Exception as exc:
        logger.error("polling: excepción inesperada — %s", exc, exc_info=True)
        s = _error_state("error", str(exc))

    return s, session_key, org_id, alerted


def _error_state(status: str, message: str = "") -> UsageState:
    return replace(EMPTY_STATE, session_status=status, error_message=message, last_updated=_now())


def _now() -> str:
    return datetime.datetime.now(tz=datetime.timezone.utc).isoformat()

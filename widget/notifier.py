import logging
import subprocess
import sys

logger = logging.getLogger(__name__)


def notify(title: str, message: str) -> None:
    """Envía notificación del sistema. plyer primario; notify-send como fallback en Linux."""
    if _try_plyer(title, message):
        return
    if sys.platform.startswith("linux"):
        _notify_send(title, message)
    else:
        logger.warning("notifier: sin fallback para la plataforma %s", sys.platform)


def _try_plyer(title: str, message: str) -> bool:
    try:
        from plyer import notification  # lazy import — plyer es opcional
        notification.notify(title=title, message=message, app_name="Claude Usage Widget")
        return True
    except Exception as exc:
        logger.warning("notifier: plyer falló (%s); intentando fallback", exc)
        return False


def _notify_send(title: str, message: str) -> None:
    try:
        subprocess.run(
            ["notify-send", "--app-name=claude-usage-widget", title, message],
            check=True,
            capture_output=True,
            timeout=5,
        )
    except Exception as exc:
        logger.error("notifier: notify-send falló — %s", exc)

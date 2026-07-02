import logging
import subprocess
import sys
from typing import Callable

from widget.state import UsageState

logger = logging.getLogger(__name__)

_TITLE_OK = "Claude Usage Widget"
# El backend Xorg de pystray fija el título vía WM_NAME (STRING/Latin-1),
# así que caracteres fuera de Latin-1 como el guion largo rompen el set_wm_name.
_TITLE_ERR = "Claude Usage - sesión caducada"

try:
    import pystray
    from PIL import Image, ImageDraw
    _UI_AVAILABLE = True
except ImportError:
    _UI_AVAILABLE = False


def _check_appindicator() -> bool:
    """Comprueba si AppIndicator GNOME Shell extension está habilitada (solo Linux)."""
    if not sys.platform.startswith("linux"):
        return True
    try:
        result = subprocess.run(
            ["gnome-extensions", "info", "appindicatorsupport@rgcjonas.gmail.com"],
            capture_output=True,
            timeout=3,
        )
        return result.returncode == 0
    except Exception:
        return False


def _make_icon(*, error: bool):
    """Círculo verde (normal) o rojo (error), 64×64 RGBA."""
    size = 64
    img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    color = (220, 50, 50, 255) if error else (50, 180, 50, 255)
    draw.ellipse([4, 4, size - 4, size - 4], fill=color)
    return img


class TrayIcon:
    """Icono de bandeja del sistema. `run()` es bloqueante; lanzar en hilo daemon."""

    def __init__(
        self,
        on_open: Callable,
        on_settings: Callable,
        on_quit: Callable,
    ) -> None:
        self._on_open = on_open
        self._on_settings = on_settings
        self._on_quit = on_quit
        self._icon = None

    def run(self) -> None:
        """Arranca el icono de bandeja. Bloqueante."""
        if sys.platform.startswith("linux") and not _check_appindicator():
            logger.warning(
                "TrayIcon: AppIndicator GNOME Shell extension no detectada. "
                "El icono puede no aparecer. Instala 'AppIndicator and KStatusNotifierItem Support' "
                "desde extensions.gnome.org y reinicia la sesión."
            )

        if not _UI_AVAILABLE:
            logger.error("TrayIcon: pystray/Pillow no instalados — icono de bandeja desactivado")
            return

        menu = pystray.Menu(
            pystray.MenuItem(
                "Abrir", lambda icon, item: self._on_open(), default=True
            ),
            pystray.MenuItem("Ajustes", lambda icon, item: self._on_settings()),
            pystray.Menu.SEPARATOR,
            pystray.MenuItem("Salir", lambda icon, item: self._on_quit()),
        )
        self._icon = pystray.Icon("claude-usage", _make_icon(error=False), _TITLE_OK, menu)
        self._icon.run()

    def stop(self) -> None:
        """Para el icono de bandeja. Seguro desde cualquier hilo."""
        if self._icon is not None:
            try:
                self._icon.stop()
            except Exception as exc:
                logger.warning("TrayIcon.stop: %s", exc)

    def apply_state(self, s: UsageState) -> None:
        """Actualiza color del icono y tooltip según el estado. Seguro desde cualquier hilo."""
        if self._icon is None or not _UI_AVAILABLE:
            return
        error = s.session_status in ("expired", "error")
        try:
            self._icon.icon = _make_icon(error=error)
            self._icon.title = _TITLE_ERR if error else _TITLE_OK
        except Exception as exc:
            logger.warning("TrayIcon.apply_state: %s", exc)

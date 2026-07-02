import logging
import threading
from typing import Optional

from widget.config import load_config
from widget.polling import polling_loop
from widget.state import EMPTY_STATE, UsageState
from widget.ui.popup import PopupWindow
from widget.ui.settings import open_settings
from widget.ui.tray import TrayIcon

logger = logging.getLogger(__name__)


class App:
    """Orquestador principal. `run()` bloquea en el hilo principal."""

    def __init__(self) -> None:
        self.config = load_config()
        self.state: UsageState = EMPTY_STATE
        self.stop_event = threading.Event()
        self._root = None
        self._popup: Optional[PopupWindow] = None
        self._tray: Optional[TrayIcon] = None

    # ── Entrada pública ──────────────────────────────────────────────────

    def run(self) -> None:
        """Punto de entrada. Debe llamarse desde el hilo principal."""
        self._init_root()

        if self.config.browser == "":
            from widget.onboarding import run_onboarding
            cfg = run_onboarding(self._root)
            if cfg is None:
                logger.info("App: onboarding cancelado — saliendo")
                return
            self.config = cfg

        self._tray = TrayIcon(
            on_open=self._on_open,
            on_settings=self._on_settings,
            on_quit=self.stop,
        )
        if self._root is not None:
            self._popup = PopupWindow(self._root, self.config, on_settings=self._on_settings)

        self._start_threads()

        if self._root is not None:
            self._root.mainloop()
        else:
            self.stop_event.wait()

    def stop(self) -> None:
        """Para la app. Seguro desde cualquier hilo."""
        self.stop_event.set()
        if self._tray:
            self._tray.stop()
        if self._root:
            self._root.after(0, self._root.quit)

    # ── Despacho de estado ───────────────────────────────────────────────

    def dispatch_state(self, s: UsageState) -> None:
        """Encolado al hilo principal vía root.after. Llamado desde el hilo de polling."""
        self.state = s
        if self._root is not None:
            self._root.after(0, self._apply_state, s)

    def _apply_state(self, s: UsageState) -> None:
        if self._tray:
            self._tray.apply_state(s)
        if self._popup:
            self._popup.update_state(s)

    # ── Callbacks del tray ───────────────────────────────────────────────

    def _on_open(self) -> None:
        if self._root and self._popup:
            self._root.after(0, self._popup.show)

    def _on_settings(self) -> None:
        if self._root:
            self._root.after(0, lambda: open_settings(self._root, self.config))

    # ── Inicialización interna ───────────────────────────────────────────

    def _init_root(self) -> None:
        try:
            import customtkinter as ctk
            ctk.set_appearance_mode("dark")
            self._root = ctk.CTk()
            self._root.withdraw()
        except ImportError:
            logger.warning("App: customtkinter no disponible — modo sin UI")

    def _start_threads(self) -> None:
        threading.Thread(
            target=self._tray.run if self._tray else lambda: None,
            daemon=True,
            name="tray",
        ).start()
        threading.Thread(
            target=lambda: polling_loop(self.config, self.stop_event, self.dispatch_state),
            daemon=True,
            name="polling",
        ).start()


def main() -> None:
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(name)s: %(message)s")
    App().run()


if __name__ == "__main__":
    main()

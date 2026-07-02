import logging
from dataclasses import replace

from widget.config import Config, save_config
from widget.formatting import bar_color_for_pct, format_time_ago, format_time_remaining
from widget.state import UsageState

logger = logging.getLogger(__name__)

try:
    import customtkinter as ctk
    _UI_AVAILABLE = True
except ImportError:
    _UI_AVAILABLE = False

_BG = "#1c1c1e"
_BG_ALT = "#2a2a2c"
_FG_MUTED = "#9a9a9e"
_BAR_WIDTH = 280


class PopupWindow:
    """Popup flotante con barras de uso. Debe crearse y usarse desde el hilo principal."""

    def __init__(self, root, config: Config) -> None:
        self._root = root
        self._config = config
        self._window = None

        if not _UI_AVAILABLE:
            logger.error("PopupWindow: customtkinter no instalado — popup desactivado")
            return

        self._window = ctk.CTkToplevel(root)
        self._window.title("Claude Usage")
        self._window.resizable(False, False)
        self._window.configure(fg_color=_BG)
        self._window.withdraw()
        # El botón de cierre nativo (X) destruye el Toplevel por defecto.
        # Este objeto vive todo el ciclo de vida de la app y se reutiliza
        # en cada apertura, así que cerrar debe ocultar, no destruir.
        self._window.protocol("WM_DELETE_WINDOW", self.hide)
        self._build_ui()

    # ── Construcción de UI ───────────────────────────────────────────────

    def _build_metric(self, parent, title: str) -> dict:
        """Fila de métrica: título+% arriba, barra coloreada, reset debajo."""
        row = ctk.CTkFrame(parent, fg_color="transparent")
        row.pack(fill="x", padx=16, pady=(10, 8))

        header = ctk.CTkFrame(row, fg_color="transparent")
        header.pack(fill="x")
        ctk.CTkLabel(header, text=title, font=("", 13, "bold")).pack(side="left")
        pct_label = ctk.CTkLabel(header, text="—", font=("", 13, "bold"))
        pct_label.pack(side="right")

        bar = ctk.CTkProgressBar(row, width=_BAR_WIDTH, height=8)
        bar.set(0)
        bar.pack(fill="x", pady=(6, 4))

        reset_label = ctk.CTkLabel(row, text="—", font=("", 11), text_color=_FG_MUTED)
        reset_label.pack(anchor="w")

        return {"pct_label": pct_label, "bar": bar, "reset_label": reset_label}

    def _build_ui(self) -> None:
        self._session = self._build_metric(self._window, "Sesión actual")

        # Cabecera Weekly colapsable
        header = ctk.CTkFrame(self._window, fg_color="transparent")
        header.pack(fill="x", padx=16, pady=(2, 0))
        self._arrow = ctk.CTkButton(
            header, text=self._arrow_text(), width=20, height=20, fg_color="transparent",
            hover_color=_BG_ALT, command=self._toggle_weekly,
        )
        self._arrow.pack(side="left")
        ctk.CTkLabel(header, text=" Semanal", text_color=_FG_MUTED, font=("", 11)).pack(
            side="left"
        )

        # Contenido Weekly (colapsado por defecto)
        self._weekly_frame = ctk.CTkFrame(self._window, fg_color="transparent")
        self._weekly = self._build_metric(self._weekly_frame, "Semanal")

        if self._config.weekly_expanded:
            self._weekly_frame.pack(fill="x")

        # Pie: última actualización
        ctk.CTkFrame(self._window, fg_color=_BG_ALT, height=1).pack(
            fill="x", padx=16, pady=(4, 0)
        )
        footer = ctk.CTkFrame(self._window, fg_color="transparent")
        footer.pack(fill="x", padx=16, pady=(8, 12))
        self._lbl_updated = ctk.CTkLabel(
            footer, text="—", font=("", 10), text_color=_FG_MUTED
        )
        self._lbl_updated.pack(anchor="w")

    # ── Interfaz pública ─────────────────────────────────────────────────

    def _update_metric(self, widgets: dict, pct: float, reset_at: str) -> None:
        widgets["bar"].configure(progress_color=bar_color_for_pct(pct))
        widgets["bar"].set(max(0.0, min(1.0, pct / 100.0)))
        widgets["pct_label"].configure(text=f"{pct:.0f}%")
        widgets["reset_label"].configure(text=f"Reinicio en {format_time_remaining(reset_at)}")

    def update_state(self, s: UsageState) -> None:
        """Actualiza barras y etiquetas. Llamar siempre desde el hilo principal."""
        if self._window is None:
            return
        try:
            self._update_metric(self._session, s.five_hour_pct, s.five_hour_reset_at)
            self._update_metric(self._weekly, s.seven_day_pct, s.seven_day_reset_at)
            self._lbl_updated.configure(text=f"Actualizado {format_time_ago(s.last_updated)}")
        except Exception as exc:
            logger.warning("PopupWindow.update_state: %s", exc)

    def show(self) -> None:
        if self._window is None:
            return
        try:
            self._window.deiconify()
            self._window.lift()
            # GNOME/Mutter (X11 y Wayland) ignora peticiones de foco/raise
            # que no vengan de una interacción directa con el WM, así que
            # `lift()` solo no basta: la ventana queda mapeada pero detrás
            # de otras. `-topmost` sí lo respeta el WM.
            self._window.attributes("-topmost", True)
            self._window.focus_force()
            self._window.after(200, lambda: self._window.attributes("-topmost", False))
            self._root.bind_all("<Button-1>", self._on_global_click, add="+")
        except Exception as exc:
            logger.warning("PopupWindow.show: %s", exc)

    def hide(self) -> None:
        if self._window is None:
            return
        try:
            self._window.withdraw()
            self._root.unbind_all("<Button-1>")
        except Exception as exc:
            logger.warning("PopupWindow.hide: %s", exc)

    # ── Lógica interna ───────────────────────────────────────────────────

    def _toggle_weekly(self) -> None:
        self._config = replace(self._config, weekly_expanded=not self._config.weekly_expanded)
        save_config(self._config)
        if self._config.weekly_expanded:
            self._weekly_frame.pack(fill="x")
        else:
            self._weekly_frame.pack_forget()
        self._arrow.configure(text=self._arrow_text())

    def _arrow_text(self) -> str:
        return "▼" if self._config.weekly_expanded else "▶"

    def _on_global_click(self, event) -> None:
        """Cierra el popup si el click ocurre fuera de sus límites."""
        if self._window is None:
            return
        try:
            wx = self._window.winfo_rootx()
            wy = self._window.winfo_rooty()
            ww = self._window.winfo_width()
            wh = self._window.winfo_height()
            if not (wx <= event.x_root <= wx + ww and wy <= event.y_root <= wy + wh):
                self.hide()
        except Exception as exc:
            logger.warning("PopupWindow._on_global_click: %s", exc)

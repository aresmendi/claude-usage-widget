import logging

from widget.config import Config, save_config

logger = logging.getLogger(__name__)

try:
    import customtkinter as ctk
    _UI_AVAILABLE = True
except ImportError:
    _UI_AVAILABLE = False

_BG = "#1c1c1e"


def open_settings(root, config: Config) -> None:
    """Abre el diálogo modal de ajustes.

    Muta `config` in-place (Config no es frozen) para que el hilo de polling,
    que comparte la misma instancia, recoja los cambios sin reinicio.
    Debe llamarse desde el hilo principal.
    """
    if root is None or not _UI_AVAILABLE:
        logger.warning("settings: customtkinter no disponible — diálogo desactivado")
        return

    from widget.cookie_reader import SUPPORTED_BROWSERS

    browsers = list(SUPPORTED_BROWSERS.keys()) or [config.browser or "firefox"]

    win = ctk.CTkToplevel(root)
    win.title("Ajustes")
    win.resizable(False, False)
    win.configure(fg_color=_BG)
    win.grab_set()
    win.lift()
    win.attributes("-topmost", True)
    win.focus_force()

    ctk.CTkLabel(win, text="Navegador con sesión activa:").pack(
        padx=20, pady=(16, 4), anchor="w"
    )
    combo = ctk.CTkComboBox(win, values=browsers, state="readonly")
    combo.set(config.browser if config.browser in browsers else browsers[0])
    combo.pack(padx=20, pady=(0, 12), fill="x")

    ctk.CTkLabel(win, text="Umbral de aviso (%):").pack(padx=20, pady=(0, 4), anchor="w")
    threshold_var = ctk.StringVar(value=str(int(config.alert_threshold)))
    ctk.CTkEntry(win, textvariable=threshold_var).pack(padx=20, pady=(0, 4), fill="x")

    status_lbl = ctk.CTkLabel(win, text="", text_color="red")
    status_lbl.pack(padx=20, pady=(0, 4))

    def on_save() -> None:
        try:
            threshold = float(threshold_var.get())
        except ValueError:
            status_lbl.configure(text="Umbral inválido — debe ser un número")
            return
        if not (0.0 <= threshold <= 100.0):
            status_lbl.configure(text="Umbral fuera de rango (0-100)")
            return

        config.browser = combo.get()
        config.alert_threshold = threshold
        save_config(config)
        win.destroy()

    btn_row = ctk.CTkFrame(win, fg_color="transparent")
    btn_row.pack(pady=(8, 16))
    ctk.CTkButton(btn_row, text="Guardar", command=on_save).pack(side="left", padx=6)
    ctk.CTkButton(btn_row, text="Cancelar", command=win.destroy).pack(side="left", padx=6)

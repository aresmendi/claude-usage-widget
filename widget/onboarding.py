import logging
from typing import Optional

from widget.config import Config, save_config

logger = logging.getLogger(__name__)


def _platform_browsers() -> list[str]:
    from widget.cookie_reader import SUPPORTED_BROWSERS

    return list(SUPPORTED_BROWSERS.keys())


def run_onboarding(root) -> Optional[Config]:
    """
    Muestra el modal de primera configuración. Retorna Config si el usuario confirma,
    None si cancela. Si root es None o customtkinter no está disponible, intenta
    detección automática de navegador (modo headless).
    """
    if root is None:
        return _headless_detect()

    try:
        import customtkinter as ctk
    except ImportError:
        logger.warning("onboarding: customtkinter no disponible — detección automática")
        return _headless_detect()

    return _show_modal(root, ctk)


# ── Modal interactivo ────────────────────────────────────────────────────────


def _show_modal(root, ctk) -> Optional[Config]:
    from widget.cookie_reader import CookieError, get_session_key
    from widget.fetcher import AuthError, FetchError, fetch_usage, resolve_org_id

    result: list[Optional[Config]] = [None]
    browsers = _platform_browsers()

    win = ctk.CTkToplevel(root)
    win.title("Configuración inicial")
    win.resizable(False, False)
    win.grab_set()

    ctk.CTkLabel(
        win, text="Selecciona el navegador con sesión activa en claude.ai:"
    ).pack(padx=20, pady=(16, 4))

    combo = ctk.CTkComboBox(win, values=browsers, state="readonly")
    combo.set(browsers[0])
    combo.pack(padx=20, pady=4)

    status_lbl = ctk.CTkLabel(win, text="", wraplength=280, justify="left")
    status_lbl.pack(padx=20, pady=(0, 4))

    def on_confirm() -> None:
        browser = combo.get()
        status_lbl.configure(text="Verificando…", text_color="gray")
        win.update_idletasks()
        try:
            key = get_session_key(browser)
            org = resolve_org_id(key)
            fetch_usage(key, org)
            cfg = Config(browser=browser, alert_threshold=70.0, weekly_expanded=False)
            save_config(cfg)
            result[0] = cfg
            win.destroy()
        except (CookieError, AuthError, FetchError) as exc:
            logger.error("onboarding: fallo al verificar %r — %s", browser, exc)
            status_lbl.configure(text=f"Error: {exc}", text_color="red")

    btn_row = ctk.CTkFrame(win, fg_color="transparent")
    btn_row.pack(pady=12)
    ctk.CTkButton(btn_row, text="Confirmar", command=on_confirm).pack(side="left", padx=6)
    ctk.CTkButton(btn_row, text="Cancelar", command=win.destroy).pack(side="left", padx=6)

    win.wait_window()
    return result[0]


# ── Detección automática (headless) ──────────────────────────────────────────


def _headless_detect() -> Optional[Config]:
    from widget.cookie_reader import get_session_key
    from widget.fetcher import fetch_usage, resolve_org_id

    for browser in _platform_browsers():
        try:
            key = get_session_key(browser)
            org = resolve_org_id(key)
            fetch_usage(key, org)
            cfg = Config(browser=browser, alert_threshold=70.0, weekly_expanded=False)
            save_config(cfg)
            logger.info("onboarding: navegador detectado — %s", browser)
            return cfg
        except Exception as exc:
            logger.debug("onboarding: %s no disponible (%s)", browser, exc)

    logger.error("onboarding: no se detectó ningún navegador válido")
    return None

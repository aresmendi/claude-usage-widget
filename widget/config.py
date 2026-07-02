from __future__ import annotations

import json
import os
import sys
from dataclasses import asdict, dataclass
from pathlib import Path


@dataclass
class Config:
    browser: str = ""
    alert_threshold: float = 70.0
    weekly_expanded: bool = False


def config_path() -> Path:
    """Devuelve la ruta al fichero de configuración según la plataforma."""
    if sys.platform == "win32":
        base = Path(os.environ.get("APPDATA", Path.home() / "AppData" / "Roaming"))
    else:
        # XDG_CONFIG_HOME por defecto a ~/.config si no está definida.
        base = Path(os.environ.get("XDG_CONFIG_HOME", Path.home() / ".config"))
    return base / "claude-widget" / "config.json"


def load_config(path: Path | None = None) -> Config:
    """Lee la configuración desde disco.

    Devuelve Config() con valores por defecto si el fichero no existe
    o contiene JSON inválido; nunca lanza excepción.
    """
    p = path or config_path()
    try:
        data = json.loads(p.read_text(encoding="utf-8"))
        return Config(
            browser=str(data.get("browser", "")),
            alert_threshold=float(data.get("alert_threshold", 70.0)),
            weekly_expanded=bool(data.get("weekly_expanded", False)),
        )
    except (FileNotFoundError, json.JSONDecodeError, TypeError, ValueError):
        return Config()


def save_config(config: Config, path: Path | None = None) -> None:
    """Escribe la configuración en disco de forma inmediata.

    Crea los directorios intermedios si no existen.
    """
    p = path or config_path()
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(asdict(config), indent=2), encoding="utf-8")

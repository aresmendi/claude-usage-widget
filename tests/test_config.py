import json
from pathlib import Path

import pytest

from widget.config import Config, load_config, save_config


def test_load_config_missing_file_returns_defaults(tmp_path: Path) -> None:
    path = tmp_path / "config.json"
    cfg = load_config(path)
    assert cfg == Config()


def test_load_config_corrupt_json_returns_defaults(tmp_path: Path) -> None:
    path = tmp_path / "config.json"
    path.write_text("{not valid json", encoding="utf-8")
    cfg = load_config(path)
    assert cfg == Config()


def test_load_config_valid_file_applies_all_fields(tmp_path: Path) -> None:
    path = tmp_path / "config.json"
    data = {"browser": "firefox", "alert_threshold": 85.0, "weekly_expanded": True}
    path.write_text(json.dumps(data), encoding="utf-8")

    cfg = load_config(path)

    assert cfg.browser == "firefox"
    assert cfg.alert_threshold == 85.0
    assert cfg.weekly_expanded is True


def test_save_and_load_roundtrip(tmp_path: Path) -> None:
    path = tmp_path / "config.json"
    original = Config(browser="chrome", alert_threshold=50.0, weekly_expanded=True)

    save_config(original, path)
    recovered = load_config(path)

    assert recovered == original


def test_save_config_creates_intermediate_directories(tmp_path: Path) -> None:
    path = tmp_path / "nested" / "deep" / "config.json"
    save_config(Config(browser="firefox"), path)
    assert path.exists()


def test_weekly_expanded_persists_correctly(tmp_path: Path) -> None:
    path = tmp_path / "config.json"

    save_config(Config(weekly_expanded=True), path)
    assert load_config(path).weekly_expanded is True

    save_config(Config(weekly_expanded=False), path)
    assert load_config(path).weekly_expanded is False

from __future__ import annotations

import os
import sys
from pathlib import Path


APP_DIRNAME = "HolyWar"


def _home_fallback_dir(*parts: str) -> Path:
    return Path.home().joinpath(*parts)


def appdata_dir() -> Path:
    raw = os.environ.get("APPDATA", "").strip()
    if raw:
        return Path(raw) / APP_DIRNAME
    return _home_fallback_dir(".config", APP_DIRNAME)


def local_appdata_dir() -> Path:
    raw = os.environ.get("LOCALAPPDATA", "").strip()
    if raw:
        return Path(raw) / APP_DIRNAME
    return _home_fallback_dir(".local", "share", APP_DIRNAME)


def app_temp_dir() -> Path:
    return local_appdata_dir() / "Temp"


def bundled_project_root() -> Path:
    meipass = getattr(sys, "_MEIPASS", None)
    if isinstance(meipass, str) and meipass.strip():
        return Path(meipass)
    return Path(__file__).resolve().parents[1]


def bundled_data_dir() -> Path:
    return bundled_project_root() / "holywar" / "data"


from __future__ import annotations

import importlib
import pkgutil
import unicodedata
from collections.abc import Iterator
from pathlib import Path
from typing import Any


def _norm_name(name: str) -> str:
    value = unicodedata.normalize("NFKD", name or "")
    value = "".join(ch for ch in value if not unicodedata.combining(ch))
    return value.strip().lower()


_MODULE_MTIMES: dict[str, float] = {}


def _import_or_reload_if_changed(module_name: str):
    module = importlib.import_module(module_name)
    origin = getattr(getattr(module, "__spec__", None), "origin", None) or getattr(module, "__file__", None)
    if not isinstance(origin, str) or not origin:
        return module
    try:
        mtime = Path(origin).stat().st_mtime
    except OSError:
        return module
    previous = _MODULE_MTIMES.get(module_name)
    if previous is None:
        _MODULE_MTIMES[module_name] = float(mtime)
        return module
    if float(mtime) > float(previous):
        module = importlib.reload(module)
        _MODULE_MTIMES[module_name] = float(mtime)
    return module


def iter_card_scripts() -> Iterator[tuple[str, dict[str, Any]]]:
    import holywar.effects.card_scripts.cards as scripts_pkg

    seen: set[str] = set()
    for mod in pkgutil.walk_packages(scripts_pkg.__path__, scripts_pkg.__name__ + "."):
        module = _import_or_reload_if_changed(mod.name)
        card_name = getattr(module, "CARD_NAME", None)
        spec = getattr(module, "SCRIPT", None)
        if not isinstance(card_name, str) or not card_name.strip():
            continue
        if not isinstance(spec, dict):
            continue
        key = _norm_name(card_name)
        if key in seen:
            continue
        seen.add(key)
        yield card_name, dict(spec)

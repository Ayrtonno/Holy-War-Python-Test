from __future__ import annotations

import importlib
import pkgutil
import unicodedata
from collections.abc import Iterator
from typing import Any


def _norm_name(name: str) -> str:
    value = unicodedata.normalize("NFKD", name or "")
    value = "".join(ch for ch in value if not unicodedata.combining(ch))
    return value.strip().lower()


def iter_card_scripts() -> Iterator[tuple[str, dict[str, Any]]]:
    import holywar.effects.card_scripts.cards as scripts_pkg

    seen: set[str] = set()
    for mod in pkgutil.walk_packages(scripts_pkg.__path__, scripts_pkg.__name__ + "."):
        module = importlib.import_module(mod.name)
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

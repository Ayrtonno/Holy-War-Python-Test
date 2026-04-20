from __future__ import annotations

import importlib
import pkgutil

from holywar.effects.runtime import runtime_cards

_MODULES_LOADED = False


def _load_card_modules() -> None:
    global _MODULES_LOADED
    if _MODULES_LOADED:
        return
    import holywar.effects.cards as cards_pkg

    for module_info in pkgutil.walk_packages(cards_pkg.__path__, cards_pkg.__name__ + "."):
        importlib.import_module(module_info.name)
    _MODULES_LOADED = True


def resolve_enter_effect(engine, player_idx: int, uid: str) -> str | None:
    _load_card_modules()
    out = runtime_cards.resolve_enter(engine, player_idx, uid)
    if out is None:
        return None
    text = str(out).strip()
    if not text or text.lower() == "none":
        return None
    return text


def resolve_card_effect(engine, player_idx: int, uid: str, target: str | None) -> str:
    _load_card_modules()
    return str(runtime_cards.resolve_play(engine, player_idx, uid, target))


def resolve_activated_effect(engine, player_idx: int, uid: str, target: str | None) -> str:
    _load_card_modules()
    return str(runtime_cards.resolve_activate(engine, player_idx, uid, target))

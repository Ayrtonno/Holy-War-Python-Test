from __future__ import annotations

import importlib
import pkgutil

from holywar.effects import legacy_handlers
from holywar.effects.registry import NOT_HANDLED, get_activate, get_enter, get_play

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
    inst = engine.state.instances[uid]
    handler = get_enter(inst.definition.name)
    if handler is not None:
        out = handler(engine, player_idx, uid)
        if out is not NOT_HANDLED:
            return out
    return legacy_handlers.resolve_enter_effect(engine, player_idx, uid)


def resolve_card_effect(engine, player_idx: int, uid: str, target: str | None) -> str:
    _load_card_modules()
    inst = engine.state.instances[uid]
    handler = get_play(inst.definition.name)
    if handler is not None:
        out = handler(engine, player_idx, uid, target)
        if out is not NOT_HANDLED:
            return out
    return legacy_handlers.resolve_card_effect(engine, player_idx, uid, target)


def resolve_activated_effect(engine, player_idx: int, uid: str, target: str | None) -> str:
    _load_card_modules()
    inst = engine.state.instances[uid]
    handler = get_activate(inst.definition.name)
    if handler is not None:
        out = handler(engine, player_idx, uid, target)
        if out is not NOT_HANDLED:
            return str(out)
    return legacy_handlers.resolve_activated_effect(engine, player_idx, uid, target)

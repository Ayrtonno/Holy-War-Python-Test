from __future__ import annotations

from holywar.effects.runtime import runtime_cards

def resolve_enter_effect(engine, player_idx: int, uid: str) -> str | None:
    out = runtime_cards.resolve_enter(engine, player_idx, uid)
    if out is None:
        return None
    text = str(out).strip()
    if not text or text.lower() == "none":
        return None
    return text


def resolve_card_effect(engine, player_idx: int, uid: str, target: str | None) -> str:
    return str(runtime_cards.resolve_play(engine, player_idx, uid, target))


def resolve_activated_effect(engine, player_idx: int, uid: str, target: str | None) -> str:
    return str(runtime_cards.resolve_activate(engine, player_idx, uid, target))

from __future__ import annotations

from holywar.effects.registry import NOT_HANDLED
from holywar.effects.registry import register_enter

CARD_NAME = 'Odino'

@register_enter(CARD_NAME)
def on_enter(engine, player_idx: int, uid: str):
    return NOT_HANDLED

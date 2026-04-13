from __future__ import annotations

from holywar.effects.registry import NOT_HANDLED
from holywar.effects.registry import register_play

CARD_NAME = 'Pietra Nera'

@register_play(CARD_NAME)
def on_play(engine, player_idx: int, uid: str, target: str | None):
    return NOT_HANDLED

from __future__ import annotations

import unicodedata

from holywar.effects.registry import NOT_HANDLED
from holywar.effects.registry import register_enter

CARD_NAME = 'Pianta Carnivora'


def _norm(text: str) -> str:
    value = unicodedata.normalize("NFKD", text)
    value = "".join(ch for ch in value if not unicodedata.combining(ch))
    return value.strip().lower()


@register_enter(CARD_NAME)
def on_enter(engine, player_idx: int, uid: str):
    # Se "Insetto della Palude" e' sul tuo terreno: +2 Fede e +2 Forza.
    has_palude = any(
        _norm(engine.state.instances[s_uid].definition.name) == _norm("Insetto della Palude")
        for s_uid in engine.all_saints_on_field(player_idx)
    )
    if not has_palude:
        return NOT_HANDLED
    inst = engine.state.instances[uid]
    inst.current_faith = (inst.current_faith or 0) + 2
    inst.blessed.append("buff_str:2")
    return f"{engine.state.players[player_idx].name} attiva Pianta Carnivora: +2 Fede e +2 Forza."

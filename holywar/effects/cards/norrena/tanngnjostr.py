from __future__ import annotations

import unicodedata

from holywar.effects.registry import NOT_HANDLED, register_activate

CARD_NAME = 'Tanngnjostr'


def _norm(text: str) -> str:
    value = unicodedata.normalize('NFKD', text)
    value = ''.join(ch for ch in value if not unicodedata.combining(ch))
    return value.strip().lower()


@register_activate(CARD_NAME)
def on_activate(engine, player_idx: int, uid: str, target: str | None):
    player = engine.state.players[player_idx]
    if uid not in (player.attack + player.defense):
        return 'Tanngnjostr deve essere sul terreno per attivare l\'abilita.'

    thor_uid = None
    for s_uid in engine.all_saints_on_field(player_idx):
        if _norm(engine.state.instances[s_uid].definition.name) == _norm('Thor'):
            thor_uid = s_uid
            break
    if thor_uid is None:
        return 'Serve Thor sul terreno per attivare Tanngnjostr.'

    engine.remove_from_board_no_sin(player_idx, uid)
    thor = engine.state.instances[thor_uid]
    thor.current_faith = (thor.current_faith or 0) + 4
    engine.state.log(f"{player.name} sacrifica Tanngnjostr: Thor ottiene +4 Fede.")
    return 'Abilita Tanngnjostr risolta.'

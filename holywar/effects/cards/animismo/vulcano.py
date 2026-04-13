from __future__ import annotations

from holywar.effects.registry import NOT_HANDLED, register_activate

CARD_NAME = 'Vulcano'


def _resolve_target(engine, owner_idx: int, target: str | None):
    if target is None or not target.strip():
        return None, None
    raw = target.strip().lower()
    if ':' in raw:
        side, code = raw.split(':', 1)
        if side in {'o', 'opp', 'enemy'}:
            idx = 1 - owner_idx
        elif side in {'s', 'self', 'me', 'own'}:
            idx = owner_idx
        else:
            idx = 1 - owner_idx
        uid = engine.resolve_board_uid(idx, code)
        return idx, uid
    # default: prova avversario, poi proprietario
    idx = 1 - owner_idx
    uid = engine.resolve_board_uid(idx, raw)
    if uid is not None:
        return idx, uid
    uid = engine.resolve_board_uid(owner_idx, raw)
    return owner_idx, uid


@register_activate(CARD_NAME)
def on_activate(engine, player_idx: int, uid: str, target: str | None):
    if not engine.can_activate_once_per_turn(uid):
        return 'Vulcano: abilita gia usata in questo turno.'

    owner_idx, target_uid = _resolve_target(engine, player_idx, target)
    if target_uid is None or owner_idx is None:
        return 'Vulcano: bersaglio non valido (usa es. o:a1, o:r1, o:b, s:a1).'

    target_name = engine.state.instances[target_uid].definition.name
    engine.destroy_any_card(owner_idx, target_uid)
    engine.mark_activated_this_turn(uid)
    engine.state.log(f"{engine.state.players[player_idx].name} attiva Vulcano e distrugge {target_name}.")
    return 'Abilita Vulcano risolta.'

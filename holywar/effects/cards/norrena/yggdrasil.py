from __future__ import annotations

import unicodedata

from holywar.effects.registry import NOT_HANDLED, register_activate

CARD_NAME = 'Yggdrasil'


def _norm(text: str) -> str:
    value = unicodedata.normalize('NFKD', text)
    value = ''.join(ch for ch in value if not unicodedata.combining(ch))
    return value.strip().lower()


def _has_named_saint_on_field(engine, player_idx: int, name: str) -> bool:
    key = _norm(name)
    for s_uid in engine.all_saints_on_field(player_idx):
        if _norm(engine.state.instances[s_uid].definition.name) == key:
            return True
    return False


@register_activate(CARD_NAME)
def on_activate(engine, player_idx: int, uid: str, target: str | None):
    if not engine.can_activate_once_per_turn(uid):
        return 'Yggdrasil: abilita gia usata in questo turno.'

    player = engine.state.players[player_idx]
    mode = _norm(target or '')

    # Modalita buff su santo (default se target tipo a1/d1)
    if mode.startswith('a') or mode.startswith('d') or mode.startswith('buff') or mode == '':
        target_code = None
        if ':' in mode:
            _prefix, target_code = mode.split(':', 1)
        elif mode.startswith('a') or mode.startswith('d'):
            target_code = mode
        else:
            for i, s_uid in enumerate(player.attack):
                if s_uid is not None:
                    target_code = f'a{i+1}'
                    break
            if target_code is None:
                for i, s_uid in enumerate(player.defense):
                    if s_uid is not None:
                        target_code = f'd{i+1}'
                        break
        saint = engine.resolve_target_saint(player_idx, target_code)
        if saint is not None:
            saint.current_faith = (saint.current_faith or 0) + 2
            saint.blessed.append('buff_str:2')
            engine.mark_activated_this_turn(uid)
            return f"Yggdrasil: {saint.definition.name} ottiene +2 Fede e +2 Forza."

    # Modalita recupero artefatto dal cimitero -> mano
    if mode in {'artifact', 'artefatto', 'grave_artifact'}:
        for g_uid in list(player.graveyard):
            if _norm(engine.state.instances[g_uid].definition.card_type) == 'artefatto':
                if engine.move_graveyard_card_to_hand(player_idx, g_uid):
                    engine.mark_activated_this_turn(uid)
                    return f"Yggdrasil: recuperato {engine.state.instances[g_uid].definition.name} in mano."
        return 'Yggdrasil: nessun artefatto nel cimitero.'

    # Modalita pesca condizionata
    if mode in {'draw', 'pesca'}:
        names = {_norm(engine.state.instances[s_uid].definition.name) for s_uid in engine.all_saints_on_field(player_idx)}
        if len(names) >= 3:
            drawn = engine.draw_cards(player_idx, 1)
            engine.mark_activated_this_turn(uid)
            return f'Yggdrasil: pesca {drawn} carta.'
        return 'Yggdrasil: servono almeno 3 santi con nomi diversi.'

    # Modalita warcry Thor+Odino
    if mode in {'warcry', 'thor_odino'}:
        if _has_named_saint_on_field(engine, player_idx, 'Thor') and _has_named_saint_on_field(engine, player_idx, 'Odino'):
            for s_uid in engine.all_saints_on_field(player_idx):
                engine.state.instances[s_uid].blessed.append('buff_str:1')
            engine.mark_activated_this_turn(uid)
            return 'Yggdrasil: tutti i tuoi santi ottengono +1 Forza.'
        return 'Yggdrasil: servono Thor e Odino in campo.'

    return 'Yggdrasil: target/modalita non valida.'

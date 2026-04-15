from __future__ import annotations

import unicodedata

from holywar.effects.registry import register_play

CARD_NAME = "Ricerca Archeologica"


def _norm(text: str) -> str:
    value = unicodedata.normalize("NFKD", text or "")
    value = "".join(ch for ch in value if not unicodedata.combining(ch))
    return value.strip().lower()


@register_play(CARD_NAME)
def on_play(engine, player_idx: int, uid: str, target: str | None):
    state = engine.state
    player = state.players[player_idx]
    artifacts = [
        d_uid
        for d_uid in player.deck
        if _norm(state.instances[d_uid].definition.card_type) == "artefatto"
    ]
    if not artifacts:
        return "Ricerca Archeologica: nessun artefatto nel reliquiario."

    chosen_uid = None
    desired = (target or "").strip()
    if desired:
        desired_key = _norm(desired)
        if ":" in desired_key:
            zone, name = desired_key.split(":", 1)
            if zone in {"deck", "relicario"}:
                desired_key = name.strip()
        for d_uid in artifacts:
            if _norm(state.instances[d_uid].definition.name) == desired_key:
                chosen_uid = d_uid
                break
        if chosen_uid is None:
            return "Ricerca Archeologica: artefatto richiesto non trovato nel reliquiario."
    elif len(artifacts) == 1:
        chosen_uid = artifacts[0]
    else:
        return "Ricerca Archeologica: scegli un artefatto del reliquiario."

    if not engine.move_deck_card_to_hand(player_idx, chosen_uid):
        return "Ricerca Archeologica: impossibile aggiungere carta alla mano."

    engine.rules_api(player_idx).emit("on_player_searches_relicario", card_found=chosen_uid)
    state.log(f"{player.name} usa Ricerca Archeologica e aggiunge {state.instances[chosen_uid].definition.name}.")
    return "Ricerca Archeologica risolta."

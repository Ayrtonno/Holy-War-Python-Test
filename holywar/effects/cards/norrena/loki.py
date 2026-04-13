from __future__ import annotations

from holywar.effects.registry import NOT_HANDLED
from holywar.effects.registry import register_activate

CARD_NAME = 'Loki'

def _norm(text: str) -> str:
    import unicodedata

    value = unicodedata.normalize("NFKD", text)
    value = "".join(ch for ch in value if not unicodedata.combining(ch))
    return value.strip().lower()


@register_activate(CARD_NAME)
def on_activate(engine, player_idx: int, uid: str, target: str | None):
    player = engine.state.players[player_idx]
    if uid not in (player.attack + player.defense):
        return "Loki deve essere sul terreno per attivare l'abilita."

    # Sacrifica Loki senza accumulare peccato.
    engine.remove_from_board_no_sin(player_idx, uid)
    engine.state.log(f"{player.name} sacrifica Loki senza accumulare Peccato.")

    requested = _norm(target or "")
    preferred: list[str]
    if requested in {"fenrir", "jormungandr"}:
        preferred = [requested]
    else:
        preferred = ["jormungandr", "fenrir"]

    summon_uid = None
    for name in preferred:
        for h_uid in list(player.hand):
            if _norm(engine.state.instances[h_uid].definition.name) == name:
                summon_uid = h_uid
                break
        if summon_uid is not None:
            break

    if summon_uid is None:
        return "Loki attivato, ma non hai Jormungandr/Fenrir in mano."

    player.hand.remove(summon_uid)
    open_slot = None
    for idx, slot_uid in enumerate(player.attack):
        if slot_uid is None:
            open_slot = ("attack", idx)
            break
    if open_slot is None:
        for idx, slot_uid in enumerate(player.defense):
            if slot_uid is None:
                open_slot = ("defense", idx)
                break
    if open_slot is None:
        player.hand.append(summon_uid)
        return "Nessuno slot libero per evocare Jormungandr/Fenrir."

    zone, slot = open_slot
    engine.place_card_from_uid(player_idx, summon_uid, zone, slot)
    zone_label = "Attacco" if zone == "attack" else "Difesa"
    summoned_name = engine.state.instances[summon_uid].definition.name
    engine.state.log(f"{player.name} evoca {summoned_name} con l'abilita di Loki in {zone_label} {slot + 1}.")
    return f"Abilita di Loki risolta: evocato {summoned_name}."

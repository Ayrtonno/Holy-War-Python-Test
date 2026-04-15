from __future__ import annotations

from holywar.effects.registry import register_enter

CARD_NAME = "Huginn"


def _norm(text: str) -> str:
    import unicodedata

    value = unicodedata.normalize("NFKD", text or "")
    value = "".join(ch for ch in value if not unicodedata.combining(ch))
    return value.strip().lower()

@register_enter(CARD_NAME)
def on_enter(engine, player_idx: int, uid: str):
    state = engine.state
    player = state.players[player_idx]
    top = player.deck[-3:]
    if not top:
        return f"{player.name} attiva Huginn: reliquiario vuoto."
    odino_on_field = any(
        _norm(state.instances[s_uid].definition.name) == _norm("Odino")
        for s_uid in engine.all_saints_on_field(player_idx)
    )
    chosen = None
    for c_uid in reversed(top):
        inst = state.instances[c_uid]
        if odino_on_field:
            chosen = c_uid
            break
        if _norm(inst.definition.card_type) == "santo":
            chosen = c_uid
            break
    if chosen and engine.move_deck_card_to_hand(player_idx, chosen):
        engine.rules_api(player_idx).emit("on_player_searches_relicario", card_found=chosen)
        return f"{player.name} attiva Huginn e aggiunge {state.instances[chosen].definition.name} alla mano."
    return f"{player.name} attiva Huginn ma non trova un Santo valido tra le prime 3 carte."

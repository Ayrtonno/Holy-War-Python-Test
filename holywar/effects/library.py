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

# This function resolves the effect that occurs when a card enters the field. It takes the game engine, the player index, and the unique identifier of the card as parameters. It calls the `resolve_enter` method of the `runtime_cards` module to get the effect text. If the returned text is empty, "none", or not a string, it returns `None`. Otherwise, it returns the effect text as a string.
def resolve_card_effect(engine, player_idx: int, uid: str, target: str | None) -> str:
    return str(runtime_cards.resolve_play(engine, player_idx, uid, target))

# This function resolves the effect that occurs when a card is played. It takes the game engine, the player index, the unique identifier of the card, and an optional target as parameters. It calls the `resolve_play` method of the `runtime_cards` module to get the effect text and returns it as a string. This function is used to determine what happens when a card is played in the game.
def resolve_activated_effect(engine, player_idx: int, uid: str, target: str | None) -> str:
    return str(runtime_cards.resolve_activate(engine, player_idx, uid, target))

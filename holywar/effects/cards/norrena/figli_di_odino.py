from __future__ import annotations

from holywar.effects.registry import register_play

CARD_NAME = "Figli di Odino"


def _norm(text: str) -> str:
    import unicodedata

    value = unicodedata.normalize("NFKD", text)
    value = "".join(ch for ch in value if not unicodedata.combining(ch))
    return value.strip().lower()


def _has_named_saint_on_field(engine, player_idx: int, name: str) -> bool:
    key = _norm(name)
    for uid in engine.all_saints_on_field(player_idx):
        if _norm(engine.state.instances[uid].definition.name) == key:
            return True
    return False


@register_play(CARD_NAME)
def on_play(engine, player_idx: int, uid: str, target: str | None):
    state = engine.state
    player = state.players[player_idx]
    target_card = engine.resolve_target_saint(player_idx, target)
    if not target_card:
        return "Nessun bersaglio valido per Figli di Odino."
    odino = _has_named_saint_on_field(engine, player_idx, "Odino")
    thor = _has_named_saint_on_field(engine, player_idx, "Thor")
    boost = 6 if odino else 3
    target_card.blessed.append(f"buff_str:{boost}")
    if odino and thor:
        engine.draw_cards(player_idx, 1)
    state.log(f"{player.name} potenzia {target_card.definition.name} con Figli di Odino (+{boost} Forza).")
    return "Figli di Odino risolta."
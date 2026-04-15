from __future__ import annotations

from holywar.effects.registry import register_play

CARD_NAME = "Monsone"


def _norm(text: str) -> str:
    import unicodedata

    value = unicodedata.normalize("NFKD", text or "")
    value = "".join(ch for ch in value if not unicodedata.combining(ch))
    return value.strip().lower()


def _cross_value(crosses: str | None) -> int | None:
    txt = _norm(crosses or "")
    if txt in {"white", "croce bianca"}:
        return 11
    try:
        return int(float(txt))
    except ValueError:
        return None


def _parse_payload(target: str | None) -> tuple[list[str], list[str]]:
    discard_selected: list[str] = []
    return_selected: list[str] = []
    raw = (target or "").strip()
    if not raw.startswith("monsone:"):
        return discard_selected, return_selected
    body = raw[len("monsone:") :]
    for part in body.split(";"):
        part = part.strip()
        if "=" not in part:
            continue
        key, val = part.split("=", 1)
        vals = [v.strip() for v in val.split(",") if v.strip()]
        k = _norm(key)
        if k == "discard":
            discard_selected.extend(vals)
        elif k == "return":
            return_selected.extend(vals)
    return discard_selected, return_selected


def _find_field_controller(engine, uid: str) -> int | None:
    for idx in (0, 1):
        p = engine.state.players[idx]
        if uid in (p.attack + p.defense + p.artifacts) or p.building == uid:
            return idx
    return None


@register_play(CARD_NAME)
def on_play(engine, player_idx: int, uid: str, target: str | None):
    state = engine.state
    player = state.players[player_idx]
    api = engine.rules_api(player_idx)
    discard_selected, return_selected = _parse_payload(target)

    moved = 0
    seen_discard: set[str] = set()
    for h_uid in discard_selected:
        if moved >= 3 or h_uid in seen_discard:
            continue
        seen_discard.add(h_uid)
        if api.send_from_hand_to_graveyard(h_uid):
            moved += 1
    while moved < 3 and player.deck:
        d_uid = player.deck.pop()
        player.graveyard.append(d_uid)
        api.emit("on_card_sent_to_graveyard", card=d_uid, from_zone="relicario", owner=player_idx)
        moved += 1

    valid_field: set[str] = set()
    for idx in (0, 1):
        p = state.players[idx]
        for c_uid in p.attack + p.defense + p.artifacts:
            if c_uid is None:
                continue
            cv = _cross_value(state.instances[c_uid].definition.crosses)
            if cv is not None and cv <= 8:
                valid_field.add(c_uid)
        if p.building:
            cv = _cross_value(state.instances[p.building].definition.crosses)
            if cv is not None and cv <= 8:
                valid_field.add(p.building)

    returned = 0
    used: set[str] = set()
    for f_uid in return_selected:
        if returned >= 3 or f_uid in used or f_uid not in valid_field:
            continue
        used.add(f_uid)
        controller_idx = _find_field_controller(engine, f_uid)
        if controller_idx is None:
            continue
        owner_idx = state.instances[f_uid].owner
        engine._remove_from_board(state.players[controller_idx], f_uid)
        state.players[owner_idx].deck.insert(0, f_uid)
        api.emit("on_card_sent_to_relicario", card=f_uid, from_zone="field", owner=owner_idx)
        api.emit("on_card_returned_to_relicario", card=f_uid, owner=owner_idx)
        returned += 1

    engine.rng.shuffle(state.players[0].deck)
    engine.rng.shuffle(state.players[1].deck)
    api.emit("on_player_shuffles_relicario", player=0)
    api.emit("on_player_shuffles_relicario", player=1)
    return f"Monsone risolta: {moved} carte mandate al cimitero, {returned} carte rimesse nei reliquiari."

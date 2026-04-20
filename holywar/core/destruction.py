from __future__ import annotations

import unicodedata
from typing import TYPE_CHECKING

from holywar.effects.runtime import runtime_cards

if TYPE_CHECKING:
    from holywar.core.engine import GameEngine


def _norm(text: str) -> str:
    value = unicodedata.normalize("NFKD", text)
    value = "".join(ch for ch in value if not unicodedata.combining(ch))
    return value.strip().lower()


# Destroys all saints whose current Faith has reached zero or less.
def cleanup_zero_faith_saints(engine: "GameEngine") -> None:
    saint_types = {"santo", "token"}
    seen: set[str] = set()
    for board_owner in (0, 1):
        player = engine.state.players[board_owner]
        for uid in list(player.attack + player.defense):
            if uid is None or uid in seen or uid not in engine.state.instances:
                continue
            seen.add(uid)
            inst = engine.state.instances[uid]
            if _norm(inst.definition.card_type) not in saint_types:
                continue
            faith = inst.current_faith if inst.current_faith is not None else (inst.definition.faith or 0)
            if faith <= 0:
                destroy_saint_by_uid(engine, inst.owner, uid, cause="effect")


# Handles the full saint-destruction pipeline, including prevention, survival, and aftermath.
def destroy_saint_by_uid(
    engine: "GameEngine",
    owner_idx: int,
    uid: str,
    excommunicate: bool = False,
    cause: str = "effect",
) -> None:
    if uid not in engine.state.instances:
        return
    inst = engine.state.instances[uid]
    board_owner_idx = engine._find_board_owner_of_uid(uid)
    if board_owner_idx is None:
        board_owner_idx = owner_idx
    board_player = engine.state.players[board_owner_idx]
    if "moribondo_shield" in inst.blessed:
        inst.blessed.remove("moribondo_shield")
        engine.state.log(f"Moribondo annulla la distruzione di {inst.definition.name}.")
        return
    if cause == "effect":
        source_uid = str(engine.state.flags.get("_runtime_effect_source", ""))
        if source_uid and source_uid in engine.state.instances:
            source = engine.state.instances[source_uid]
            if (
                int(source.owner) != int(owner_idx)
                and _norm(source.definition.card_type) == _norm("artefatto")
                and engine._has_artifact(owner_idx, "Terra")
            ):
                engine.state.log(
                    f"Terra impedisce a {source.definition.name} di distruggere {inst.definition.name}."
                )
                return
    if "bende_consacrate" in inst.blessed:
        inst.blessed.remove("bende_consacrate")
        inst.current_faith = 1
        engine.state.log(f"Bende Consacrate salva {inst.definition.name}: rimane con 1 Fede.")
        return

    attack_slot = None
    defense_slot = None
    for i, slot_uid in enumerate(board_player.attack):
        if slot_uid == uid:
            attack_slot = i
            break
    if attack_slot is None:
        for i, slot_uid in enumerate(board_player.defense):
            if slot_uid == uid:
                defense_slot = i
                break
    from_zone = "attack" if attack_slot is not None else ("defense" if defense_slot is not None else "field")
    if attack_slot is not None:
        board_player.attack[attack_slot] = None
    if defense_slot is not None:
        board_player.defense[defense_slot] = None

    if cause == "battle":
        survival_mode = runtime_cards.get_battle_survival_mode(inst.definition.name)
        if survival_mode == "sacrifice_token_from_field":
            token_name = runtime_cards.get_battle_survival_token_name(inst.definition.name)
            token_uid = None
            if token_name:
                for s_uid in board_player.attack + board_player.defense:
                    if not s_uid:
                        continue
                    if _norm(engine.state.instances[s_uid].definition.name) == _norm(token_name):
                        token_uid = s_uid
                        break
            if token_uid is not None:
                destroy_saint_by_uid(engine, engine.state.instances[token_uid].owner, token_uid, cause="effect")
                inst.current_faith = max(
                    0,
                    runtime_cards.get_battle_survival_restore_faith(inst.definition.name) or (inst.definition.faith or 0),
                )
                if attack_slot is not None:
                    board_player.attack[attack_slot] = uid
                elif defense_slot is not None:
                    board_player.defense[defense_slot] = uid
                engine.state.log(f"{inst.definition.name} evita la distruzione sacrificando {token_name}.")
                return
        if survival_mode == "excommunicate_card_from_graveyard":
            rescue_names = {_norm(name) for name in runtime_cards.get_battle_survival_names(inst.definition.name)}
            rescue_uid = None
            for g_uid in list(board_player.graveyard):
                g_name = _norm(engine.state.instances[g_uid].definition.name)
                if g_name in rescue_names:
                    rescue_uid = g_uid
                    break
            if rescue_uid is not None:
                board_player.graveyard.remove(rescue_uid)
                board_player.excommunicated.append(rescue_uid)
                if attack_slot is not None:
                    board_player.attack[attack_slot] = uid
                elif defense_slot is not None:
                    board_player.defense[defense_slot] = uid
                inst.current_faith = max(
                    0,
                    runtime_cards.get_battle_survival_restore_faith(inst.definition.name) or (inst.definition.faith or 0),
                )
                engine.state.log(
                    f"{inst.definition.name} evita la distruzione: scomunica {engine.state.instances[rescue_uid].definition.name} "
                    "e annulla la distruzione."
                )
                return

    if _norm(inst.definition.card_type) != "token":
        sin_gain = max(0, inst.definition.faith or 0)
        if "no_sin_on_death" in inst.blessed:
            sin_gain = 0
        if engine._has_artifact(owner_idx, "Umanit????") and inst.blessed:
            sin_gain = 0
        engine.gain_sin(owner_idx, sin_gain)
        engine.state.log(
            f"{inst.definition.name} viene distrutto: {engine.state.players[owner_idx].name} guadagna {sin_gain} Peccato."
        )
    else:
        engine.state.log(f"{inst.definition.name} (Token) viene distrutto.")

    engine._emit_event(
        "on_this_card_destroyed",
        owner_idx,
        card=uid,
        by_whom=None,
        reason=cause,
    )
    engine._emit_event("on_card_destroyed_on_field", owner_idx, card=uid, by_whom=None, reason=cause)
    if excommunicate:
        engine.excommunicate_card(owner_idx, uid, from_zone_override=from_zone)
    else:
        engine.send_to_graveyard(owner_idx, uid, token_to_white=True, from_zone_override=from_zone)
    if attack_slot is not None:
        back_uid = board_player.defense[attack_slot]
        if back_uid is not None:
            board_player.attack[attack_slot] = back_uid
            board_player.defense[attack_slot] = None
            engine.state.log(
                f"{engine.state.instances[back_uid].definition.name} avanza dalla difesa all'attacco."
            )
    if cause == "battle":
        engine._emit_event("on_saint_defeated_in_battle", owner_idx, saint=uid, by_whom=None)
    else:
        engine._emit_event("on_saint_destroyed_by_effect", owner_idx, saint=uid, by_whom=None)
    engine._emit_event("on_saint_defeated_or_destroyed", owner_idx, saint=uid, reason=cause)


# Routes card destruction based on its type so callers can use one entry point.
def destroy_any_card(engine: "GameEngine", owner_idx: int, uid: str) -> None:
    if uid is None:
        return
    ctype = _norm(engine.state.instances[uid].definition.card_type)
    if ctype in {"santo", "token"}:
        destroy_saint_by_uid(engine, engine.state.instances[uid].owner, uid, cause="effect")
    else:
        engine.send_to_graveyard(owner_idx, uid)

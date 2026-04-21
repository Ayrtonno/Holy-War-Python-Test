from __future__ import annotations

from typing import TYPE_CHECKING

from holywar.core.state import ARTIFACT_SLOTS, ATTACK_SLOTS, DEFENSE_SLOTS, MAX_HAND, PlayerState

if TYPE_CHECKING:
    from holywar.core.engine import GameEngine


FIELD_ZONES = {"attack", "defense", "artifact", "building"}


# Returns the logical zone of a card for event emission and movement rules.
def locate_uid_zone(engine: "GameEngine", owner_idx: int, uid: str) -> str:
    player = engine.state.players[owner_idx]
    if uid in player.hand:
        return "hand"
    if uid in player.deck:
        return "relicario"
    if uid in player.graveyard:
        return "graveyard"
    if uid in player.excommunicated:
        return "excommunicated"
    if uid in player.attack:
        return "attack"
    if uid in player.defense:
        return "defense"
    if uid in player.artifacts:
        return "artifact"
    if player.building == uid:
        return "building"
    return "unknown"


# Finds which player's board currently owns a given card instance.
def find_board_owner_of_uid(engine: "GameEngine", uid: str) -> int | None:
    for owner_idx in (0, 1):
        player = engine.state.players[owner_idx]
        if uid in player.attack or uid in player.defense or uid == player.building:
            return owner_idx
    return None


# Removes a card from every board slot where it may be present.
def remove_from_board(engine: "GameEngine", player: PlayerState, uid: str) -> None:
    for i, slot_uid in enumerate(player.attack):
        if slot_uid == uid:
            player.attack[i] = None
    for i, slot_uid in enumerate(player.defense):
        if slot_uid == uid:
            player.defense[i] = None
    for i, slot_uid in enumerate(player.artifacts):
        if slot_uid == uid:
            player.artifacts[i] = None
    if player.building == uid:
        player.building = None


def _equipped_target_uid(engine: "GameEngine", equipment_uid: str) -> str | None:
    inst = engine.state.instances.get(equipment_uid)
    if inst is None:
        return None
    for tag in inst.blessed:
        if not isinstance(tag, str) or not tag.startswith("equipped_to:"):
            continue
        target_uid = tag.split(":", 1)[1].strip()
        if target_uid:
            return target_uid
    return None


def _clear_equipment_link(engine: "GameEngine", equipment_uid: str, target_uid: str | None = None) -> None:
    equip_inst = engine.state.instances.get(equipment_uid)
    if equip_inst is None:
        return
    if target_uid is None:
        target_uid = _equipped_target_uid(engine, equipment_uid)
    equip_inst.blessed = [
        tag for tag in equip_inst.blessed if not (isinstance(tag, str) and tag.startswith("equipped_to:"))
    ]
    if target_uid and target_uid in engine.state.instances:
        target_inst = engine.state.instances[target_uid]
        target_inst.blessed = [tag for tag in target_inst.blessed if str(tag) != f"equipped_by:{equipment_uid}"]


def cleanup_equipment_links_on_leave_field(engine: "GameEngine", uid: str) -> None:
    # If the leaving card is equipment, detach it from its host.
    host_uid = _equipped_target_uid(engine, uid)
    if host_uid:
        _clear_equipment_link(engine, uid, host_uid)

    # If the leaving card is a host, destroy attached equipment.
    attached_uids: list[str] = []
    for equipment_uid in engine.state.instances:
        if equipment_uid == uid:
            continue
        if _equipped_target_uid(engine, equipment_uid) == uid:
            attached_uids.append(equipment_uid)

    for equipment_uid in attached_uids:
        _clear_equipment_link(engine, equipment_uid, uid)
        equipment_inst = engine.state.instances.get(equipment_uid)
        if equipment_inst is None:
            continue
        equipment_owner = int(equipment_inst.owner)
        equipment_zone = locate_uid_zone(engine, equipment_owner, equipment_uid)
        if equipment_zone in FIELD_ZONES:
            send_to_graveyard(
                engine,
                equipment_owner,
                equipment_uid,
                from_zone_override=equipment_zone,
            )


# Moves a card to the graveyard while preserving event semantics and runtime cleanup.
def send_to_graveyard(
    engine: "GameEngine",
    owner_idx: int,
    uid: str,
    token_to_white: bool = False,
    from_zone_override: str | None = None,
) -> None:
    card = engine.state.instances[uid]
    board_owner_idx = find_board_owner_of_uid(engine, uid)
    if board_owner_idx is None:
        board_owner_idx = owner_idx
    player = engine.state.players[board_owner_idx]
    from_zone = from_zone_override or locate_uid_zone(engine, board_owner_idx, uid)
    grave_target_idx = owner_idx

    for tag in list(card.blessed):
        if tag.startswith("grave_to_owner:"):
            try:
                grave_target_idx = int(tag.split(":", 1)[1])
            except ValueError:
                grave_target_idx = owner_idx
            card.blessed.remove(tag)

    leaving_field = from_zone in FIELD_ZONES
    is_token = bool(getattr(card.definition, "is_token", False)) or str(card.definition.card_type).strip().lower() == "token"

    if leaving_field:
        cleanup_equipment_links_on_leave_field(engine, uid)

    if is_token and token_to_white:
        if uid not in engine.state.players[grave_target_idx].white_deck:
            engine.state.players[grave_target_idx].white_deck.insert(0, uid)

    if uid not in engine.state.players[grave_target_idx].graveyard:
        engine.state.players[grave_target_idx].graveyard.append(uid)

    remove_from_board(engine, player, uid)

    if leaving_field:
        engine._reset_card_runtime_state(uid)

    engine._emit_event(
        "on_card_sent_to_graveyard",
        owner_idx,
        card=uid,
        from_zone=from_zone,
        owner=grave_target_idx,
    )
    if leaving_field:
        engine._emit_event("on_this_card_leaves_field", owner_idx, card=uid, destination="graveyard")


# Moves a card to the excommunicated zone while preserving leave-field effects.
def excommunicate_card(
    engine: "GameEngine",
    owner_idx: int,
    uid: str,
    from_zone_override: str | None = None,
) -> None:
    board_owner_idx = find_board_owner_of_uid(engine, uid)
    if board_owner_idx is None:
        board_owner_idx = owner_idx
    player = engine.state.players[board_owner_idx]
    from_zone = from_zone_override or locate_uid_zone(engine, board_owner_idx, uid)

    leaving_field = from_zone in FIELD_ZONES

    if leaving_field:
        cleanup_equipment_links_on_leave_field(engine, uid)

    if uid not in player.excommunicated:
        player.excommunicated.append(uid)

    remove_from_board(engine, player, uid)

    if leaving_field:
        engine._reset_card_runtime_state(uid)

    engine._emit_event(
        "on_card_excommunicated",
        owner_idx,
        card=uid,
        from_zone=from_zone,
        owner=owner_idx,
    )
    if leaving_field:
        engine._emit_event("on_this_card_leaves_field", owner_idx, card=uid, destination="excommunicated")


# Restores an excommunicated card to the graveyard when an absolution effect resolves.
def absolve_card_to_graveyard(engine: "GameEngine", owner_idx: int, uid: str) -> None:
    player = engine.state.players[owner_idx]
    if uid in player.excommunicated:
        player.excommunicated.remove(uid)
        player.graveyard.append(uid)


# Removes a card from the field without applying sin penalties.
def remove_from_board_no_sin(engine: "GameEngine", owner_idx: int, uid: str) -> None:
    board_owner_idx = find_board_owner_of_uid(engine, uid)
    if board_owner_idx is None:
        board_owner_idx = owner_idx
    player = engine.state.players[board_owner_idx]
    from_zone = locate_uid_zone(engine, board_owner_idx, uid)
    leaving_field = from_zone in FIELD_ZONES

    if leaving_field:
        cleanup_equipment_links_on_leave_field(engine, uid)

    if uid not in player.graveyard:
        player.graveyard.append(uid)
    remove_from_board(engine, player, uid)

    if leaving_field:
        engine._reset_card_runtime_state(uid)

    engine._emit_event(
        "on_card_sent_to_graveyard",
        owner_idx,
        card=uid,
        from_zone=from_zone,
        owner=owner_idx,
    )
    if leaving_field:
        engine._emit_event("on_this_card_leaves_field", owner_idx, card=uid, destination="graveyard")


# Moves a deck card to the hand with the same hand-size constraints used elsewhere.
def move_deck_card_to_hand(engine: "GameEngine", player_idx: int, uid: str) -> bool:
    player = engine.state.players[player_idx]
    if uid not in player.deck:
        return False
    if len(player.hand) >= MAX_HAND:
        return False
    player.deck.remove(uid)
    player.hand.append(uid)
    return True


# Moves a graveyard card to the hand if there is available space.
def move_graveyard_card_to_hand(engine: "GameEngine", player_idx: int, uid: str) -> bool:
    player = engine.state.players[player_idx]
    if uid not in player.graveyard or len(player.hand) >= MAX_HAND:
        return False
    player.graveyard.remove(uid)
    player.hand.append(uid)
    return True


# Returns a board card to the hand and resets runtime-only state when appropriate.
def move_board_card_to_hand(engine: "GameEngine", owner_idx: int, uid: str) -> bool:
    player = engine.state.players[owner_idx]
    if len(player.hand) >= MAX_HAND:
        return False

    was_on_field = False

    if uid in player.attack:
        idx = player.attack.index(uid)
        player.attack[idx] = None
        was_on_field = True
    if uid in player.defense:
        idx = player.defense.index(uid)
        player.defense[idx] = None
        was_on_field = True
    if uid in player.artifacts:
        idx = player.artifacts.index(uid)
        player.artifacts[idx] = None
        was_on_field = True
    if player.building == uid:
        player.building = None
        was_on_field = True

    if was_on_field:
        engine._reset_card_runtime_state(uid)

    if uid not in player.hand:
        player.hand.append(uid)
    return True


# Places a graveyard card at the bottom of the deck for recycling effects.
def move_graveyard_card_to_deck_bottom(engine: "GameEngine", player_idx: int, uid: str) -> bool:
    player = engine.state.players[player_idx]
    if uid not in player.graveyard:
        return False
    player.graveyard.remove(uid)
    player.deck.insert(0, uid)
    return True


# Places a card instance directly onto the requested board zone if the slot is free.
def place_card_from_uid(engine: "GameEngine", player_idx: int, uid: str, zone: str, slot: int) -> bool:
    player = engine.state.players[player_idx]
    if zone == "attack":
        if not (0 <= slot < ATTACK_SLOTS) or player.attack[slot] is not None:
            return False
        player.attack[slot] = uid
        return True
    if zone == "defense":
        if not (0 <= slot < DEFENSE_SLOTS) or player.defense[slot] is not None:
            return False
        player.defense[slot] = uid
        return True
    return False


# Lists all currently empty board slots for the requested zone.
def empty_slots(engine: "GameEngine", player_idx: int, zone: str) -> list[int]:
    player = engine.state.players[player_idx]
    slots = player.attack if zone == "attack" else player.defense
    return [i for i, uid in enumerate(slots) if uid is None]

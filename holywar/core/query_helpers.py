from __future__ import annotations

import unicodedata
from typing import TYPE_CHECKING

from holywar.core.state import ARTIFACT_SLOTS, CardInstance
from holywar.effects.runtime import runtime_cards

if TYPE_CHECKING:
    from holywar.core.engine import GameEngine


SAINT_TYPES = {"santo", "token"}


def _norm(text: str) -> str:
    value = unicodedata.normalize("NFKD", text)
    value = "".join(ch for ch in value if not unicodedata.combining(ch))
    return value.strip().lower()


# Returns every saint or token owned by the player currently present on any board row.
def all_saints_on_field(engine: "GameEngine", player_idx: int) -> list[str]:
    out: list[str] = []
    seen: set[str] = set()
    for board_idx in (0, 1):
        player = engine.state.players[board_idx]
        for uid in player.attack + player.defense:
            if uid is None or uid in seen:
                continue
            inst = engine.state.instances.get(uid)
            if inst is None:
                continue
            if int(inst.owner) != int(player_idx):
                continue
            ctype = _norm(inst.definition.card_type)
            if ctype in SAINT_TYPES:
                out.append(uid)
                seen.add(uid)
    return out


# Returns only the saints or tokens currently occupying the player's attack row.
def all_attack_saints(engine: "GameEngine", player_idx: int) -> list[str]:
    player = engine.state.players[player_idx]
    out: list[str] = []
    for uid in player.attack:
        if uid is None:
            continue
        ctype = _norm(engine.state.instances[uid].definition.card_type)
        if ctype in SAINT_TYPES:
            out.append(uid)
    return out


# Checks whether the player currently controls a specific artifact by name.
def has_artifact(engine: "GameEngine", player_idx: int, name: str) -> bool:
    return any(
        uid and _norm(engine.state.instances[uid].definition.name) == _norm(name)
        for uid in engine.state.players[player_idx].artifacts
    )


# Counts how many copies of the named artifact are currently on the player's field.
def count_artifact(engine: "GameEngine", player_idx: int, name: str) -> int:
    return sum(
        1
        for uid in engine.state.players[player_idx].artifacts
        if uid and _norm(engine.state.instances[uid].definition.name) == _norm(name)
    )


# Checks whether the player currently controls the named building.
def has_building(engine: "GameEngine", player_idx: int, name: str) -> bool:
    uid = engine.state.players[player_idx].building
    if uid is None:
        return False
    return _norm(engine.state.instances[uid].definition.name) == _norm(name)


# Counts how many pyramid artifacts the player currently has in play.
def count_pyramids(engine: "GameEngine", player_idx: int) -> int:
    pyramid_names = {_norm("Piramide: Chefren"), _norm("Piramide: Cheope"), _norm("Piramide: Micerino")}
    return sum(
        1
        for uid in engine.state.players[player_idx].artifacts
        if uid and _norm(engine.state.instances[uid].definition.name) in pyramid_names
    )


# Reads the current seal counter stored on Altare dei Sette Sigilli.
def get_altare_sigilli(engine: "GameEngine", player_idx: int) -> int:
    uid = engine.state.players[player_idx].building
    if uid is None:
        return 0
    inst = engine.state.instances[uid]
    if _norm(inst.definition.name) != _norm("Altare dei Sette Sigilli"):
        return 0
    for tag in inst.blessed:
        if tag.startswith("sigilli:"):
            try:
                return int(tag.split(":", 1)[1])
            except ValueError:
                return 0
    return 0


# Updates the stored seal counter and refreshes dependent bonuses.
def set_altare_sigilli(engine: "GameEngine", player_idx: int, value: int) -> None:
    uid = engine.state.players[player_idx].building
    if uid is None:
        return
    inst = engine.state.instances[uid]
    if _norm(inst.definition.name) != _norm("Altare dei Sette Sigilli"):
        return
    inst.blessed = [t for t in inst.blessed if not t.startswith("sigilli:")]
    inst.blessed.append(f"sigilli:{max(0, value)}")
    refresh_custode_sigilli_bonus(engine, player_idx)


# Recomputes the Custode dei Sigilli bonus based on the current seal count.
def refresh_custode_sigilli_bonus(engine: "GameEngine", player_idx: int) -> None:
    seals = get_altare_sigilli(engine, player_idx)
    level = seals // 6
    if level <= 0:
        return
    for uid in all_saints_on_field(engine, player_idx):
        inst = engine.state.instances[uid]
        if _norm(inst.definition.name) != _norm("Custode dei Sigilli"):
            continue
        current_level = 0
        keep: list[str] = []
        for tag in inst.blessed:
            if tag.startswith("custode_bonus:"):
                try:
                    current_level = int(tag.split(":", 1)[1])
                except ValueError:
                    current_level = 0
                continue
            keep.append(tag)
        if level > current_level:
            delta = level - current_level
            inst.current_faith = (inst.current_faith or 0) + delta * 3
            keep.extend([f"buff_str:3"] * delta)
            keep.append(f"custode_bonus:{level}")
            inst.blessed = keep
        else:
            keep.append(f"custode_bonus:{current_level}")
            inst.blessed = keep


# Converts a compact target like a1 or d2 into a board zone and zero-based slot index.
def parse_zone_target(target: str | None) -> tuple[str | None, int]:
    if not target:
        return None, -1
    value = target.strip().lower()
    if len(value) != 2:
        return None, -1
    zone_char, slot_char = value[0], value[1]
    if not slot_char.isdigit():
        return None, -1
    slot = int(slot_char) - 1
    if slot < 0 or slot >= 3:
        return None, -1
    if zone_char == "a":
        return "attack", slot
    if zone_char == "d":
        return "defense", slot
    return None, -1


# Returns the first empty index in a list of slots, or None if every slot is occupied.
def first_open(slots: list[str | None]) -> int | None:
    for idx, val in enumerate(slots):
        if val is None:
            return idx
    return None


# Consumes a one-shot barrier blessing if the defender has one active.
def consume_barrier(engine: "GameEngine", defender: CardInstance) -> str | None:
    for i, tag in enumerate(list(defender.blessed)):
        if isinstance(tag, str) and tag.startswith("barrier_once:"):
            source_uid = ""
            parts = tag.split(":")
            if len(parts) >= 3:
                source_uid = parts[2].strip()
            try:
                defender.blessed.pop(i)
            except Exception:
                defender.blessed.remove(tag)
            if source_uid and source_uid in engine.state.instances:
                source_owner = int(engine.state.instances[source_uid].owner)
                source_player = engine.state.players[source_owner]
                source_in_grave = source_uid in source_player.graveyard
                if not source_in_grave:
                    engine.send_to_graveyard(source_owner, source_uid)
            return "Barriera"
    for barrier_name in ("Barriera Magica",):
        if barrier_name in defender.blessed:
            defender.blessed.remove(barrier_name)
            return barrier_name
    return None


# Applies static damage-prevention effects that reduce or cancel incoming damage.
def apply_damage_mitigation(
    engine: "GameEngine",
    target_owner_idx: int,
    damage: int,
    target_uid: str | None = None,
) -> int:
    if damage <= 0:
        return 0

    target_type = ""
    if target_uid and target_uid in engine.state.instances:
        target_type = _norm(engine.state.instances[target_uid].definition.card_type)

    player = engine.state.players[target_owner_idx]
    aura_sources: list[str] = []
    aura_sources.extend([uid for uid in player.artifacts if uid is not None])
    if player.building is not None:
        aura_sources.append(player.building)

    for source_uid in aura_sources:
        if source_uid not in engine.state.instances:
            continue
        source_name = engine.state.instances[source_uid].definition.name
        threshold = runtime_cards.get_prevent_incoming_damage_if_less_than(source_name)
        if threshold is None:
            continue
        allowed_types = {
            _norm(v) for v in runtime_cards.get_prevent_incoming_damage_to_card_types(source_name)
        }
        if allowed_types and target_type and target_type not in allowed_types:
            continue
        if damage < int(threshold):
            return 0
    return damage


# Checks and preserves turn-based no-attack curses that still apply to the attacker.
def is_attacker_blocked_this_turn(engine: "GameEngine", attacker: CardInstance) -> bool:
    keep: list[str] = []
    blocked = False
    for tag in attacker.cursed:
        if not tag.startswith("no_attack_until:"):
            keep.append(tag)
            continue
        try:
            until_turn = int(tag.split(":", 1)[1])
        except ValueError:
            continue
        if engine.state.turn_number <= until_turn:
            blocked = True
            keep.append(tag)
    attacker.cursed = keep
    return blocked


# Consumes the defender's one-per-turn attack shield when it is still active.
def consume_attack_shield(engine: "GameEngine", defender_idx: int) -> bool:
    shield = engine.state.flags.setdefault("attack_shield_turn", {})
    key = str(defender_idx)
    if int(shield.get(key, -1)) != int(engine.state.turn_number):
        return False
    shield.pop(key, None)
    return True


# Consumes a stored counter-spell charge from the opposing player.
def consume_counter_spell(engine: "GameEngine", caster_idx: int) -> bool:
    flags = engine.state.flags.setdefault("counter_spell_ready", {"0": 0, "1": 0})
    opp_key = str(1 - caster_idx)
    count = int(flags.get(opp_key, 0))
    if count <= 0:
        return False
    flags[opp_key] = count - 1
    return True


# Resolves a target string to a saint instance on the chosen player's board.
def resolve_target_saint(engine: "GameEngine", player_idx: int, target: str | None) -> CardInstance | None:
    if not target:
        return None
    value = target.strip().lower()
    if len(value) != 2:
        return None
    zone, slot = parse_zone_target(value)
    if zone not in {"attack", "defense"}:
        return None
    player = engine.state.players[player_idx]
    uid = getattr(player, zone)[slot]
    if uid is None:
        return None
    inst = engine.state.instances[uid]
    if "untargetable_effects" in inst.blessed:
        return None
    return inst


# Resolves a target string to an artifact or building uid on the chosen player's board.
def resolve_target_artifact_or_building(engine: "GameEngine", player_idx: int, target: str | None) -> str | None:
    if not target:
        return None
    value = target.strip().lower()
    player = engine.state.players[player_idx]
    if value.startswith("r") and len(value) == 2 and value[1].isdigit():
        idx = int(value[1]) - 1
        if 0 <= idx < ARTIFACT_SLOTS:
            return player.artifacts[idx]
    if value == "b":
        return player.building
    return None


# Resolves a generic board source string to the corresponding uid on the field.
def resolve_board_uid(engine: "GameEngine", player_idx: int, source: str | None) -> str | None:
    if not source:
        return None
    value = source.strip().lower()
    zone, slot = parse_zone_target(value)
    player = engine.state.players[player_idx]
    if zone in {"attack", "defense"}:
        return getattr(player, zone)[slot]
    return resolve_target_artifact_or_building(engine, player_idx, value)


# Finds the first matching card name inside the player's deck and returns its uid.
def find_card_uid_in_deck(engine: "GameEngine", player_idx: int, name: str) -> str | None:
    player = engine.state.players[player_idx]
    key = _norm(name)
    for uid in player.deck:
        if _norm(engine.state.instances[uid].definition.name) == key:
            return uid
    return None


# Finds the first matching card name inside the player's graveyard and returns its uid.
def find_card_uid_in_graveyard(engine: "GameEngine", player_idx: int, name: str) -> str | None:
    player = engine.state.players[player_idx]
    key = _norm(name)
    for uid in player.graveyard:
        if _norm(engine.state.instances[uid].definition.name) == key:
            return uid
    return None


# Returns the sorted list of expansions currently present in the loaded match state.
def available_expansions(engine: "GameEngine") -> list[str]:
    names = set()
    for inst in engine.state.instances.values():
        if inst.definition.expansion:
            names.add(inst.definition.expansion)
    return sorted(names)

from __future__ import annotations

import unicodedata
from typing import TYPE_CHECKING

from holywar.core.results import ActionResult
from holywar.core.state import ARTIFACT_SLOTS
from holywar.effects.library import resolve_card_effect, resolve_enter_effect
from holywar.effects.runtime import runtime_cards

if TYPE_CHECKING:
    from holywar.core.engine import GameEngine
    from holywar.core.state import CardInstance


SAINT_TYPES = {"santo", "token"}
QUICK_TYPES = {"benedizione", "maledizione"}


def _norm(text: str) -> str:
    value = unicodedata.normalize("NFKD", text)
    value = "".join(ch for ch in value if not unicodedata.combining(ch))
    return value.strip().lower()


def _aliases_of(inst: "CardInstance") -> list[str]:
    raw_aliases = getattr(inst.definition, "aliases", []) or []
    if isinstance(raw_aliases, str):
        return [part.strip() for part in raw_aliases.split(",") if part.strip()]
    return [str(alias).strip() for alias in raw_aliases if str(alias).strip()]


def _name_variants(inst: "CardInstance") -> set[str]:
    variants = {_norm(inst.definition.name)}
    variants.update(_norm(alias) for alias in _aliases_of(inst))
    return {v for v in variants if v}


def _name_haystack(inst: "CardInstance") -> str:
    parts = [inst.definition.name, *_aliases_of(inst)]
    return " ".join(_norm(part) for part in parts if str(part).strip())


# Validates whether the card can be played in the requested zone and context.
def validate_play_constraints(
    engine: "GameEngine",
    player_idx: int,
    card: "CardInstance",
    target: str | None,
) -> tuple[bool, str, int, str | None, int]:
    player = engine.state.players[player_idx]
    ctype = _norm(card.definition.card_type)
    place_owner_idx = player_idx
    zone: str | None = None
    slot = -1

    if ctype in SAINT_TYPES:
        if _norm(runtime_cards.get_play_owner(card.definition.name)) in {"opponent", "enemy", "other"}:
            place_owner_idx = 1 - player_idx
        if _norm(card.definition.name) == _norm("Brigante") and not engine.all_saints_on_field(player_idx):
            return False, "Per giocare Brigante devi sacrificare un tuo santo sul terreno.", place_owner_idx, zone, slot
        zone, slot = engine._parse_zone_target(target)
        if zone not in {"attack", "defense"}:
            return False, "Per un Santo/Token indica zona: a1..a3 o d1..d3", place_owner_idx, zone, slot
        current = getattr(engine.state.players[place_owner_idx], zone)[slot]
        if current is not None:
            return False, "Slot occupato.", place_owner_idx, zone, slot
    elif ctype == "artefatto":
        pass
    elif ctype == "edificio":
        if player.building:
            return False, "Hai gia un Edificio. Va distrutto prima di giocarne un altro.", place_owner_idx, zone, slot
        if _norm(card.definition.name) == _norm("Sfinge"):
            needed = {_norm("Piramide: Cheope"), _norm("Piramide: Chefren"), _norm("Piramide: Micerino")}
            present = {
                _norm(engine.state.instances[a_uid].definition.name)
                for a_uid in player.artifacts
                if a_uid is not None
            }
            if not needed.issubset(present):
                return False, "Per giocare Sfinge servono Cheope, Chefren e Micerino sul campo.", place_owner_idx, zone, slot

    return True, "", place_owner_idx, zone, slot


def _find_owned_field_uid_by_name(engine: "GameEngine", owner_idx: int, card_name: str) -> str | None:
    wanted = _norm(card_name)
    player = engine.state.players[owner_idx]
    for uid in player.attack + player.defense + player.artifacts:
        if uid and wanted in _name_variants(engine.state.instances[uid]):
            return uid
    if player.building and wanted in _name_variants(engine.state.instances[player.building]):
        return player.building
    return None


def _zone_uids_for_owner(engine: "GameEngine", owner_idx: int, zone_name: str) -> list[str]:
    player = engine.state.players[owner_idx]
    zone = _norm(zone_name)
    if zone == "field":
        out = [uid for uid in player.attack + player.defense + player.artifacts if uid]
        if player.building:
            out.append(player.building)
        return out
    if zone == "attack":
        return [uid for uid in player.attack if uid]
    if zone == "defense":
        return [uid for uid in player.defense if uid]
    if zone in {"artifact", "artifacts"}:
        return [uid for uid in player.artifacts if uid]
    if zone == "building":
        return [player.building] if player.building else []
    if zone == "hand":
        return list(player.hand)
    if zone in {"deck", "relicario"}:
        return list(player.deck)
    if zone == "graveyard":
        return list(player.graveyard)
    if zone == "excommunicated":
        return list(player.excommunicated)
    return []


def _match_requirement_filter(engine: "GameEngine", uid: str, card_filter: dict) -> bool:
    inst = engine.state.instances.get(uid)
    if inst is None:
        return False
    name_eq = _norm(str(card_filter.get("name_equals", "")))
    name_variants = _name_variants(inst)
    name_haystack = _name_haystack(inst)
    if name_eq and name_eq not in name_variants:
        return False
    name_contains = _norm(str(card_filter.get("name_contains", "")))
    if name_contains and name_contains not in name_haystack:
        return False
    name_not_contains = _norm(str(card_filter.get("name_not_contains", "")))
    if name_not_contains and name_not_contains in name_haystack:
        return False
    type_filter = {_norm(str(v)) for v in list(card_filter.get("card_type_in", []) or [])}
    if type_filter and _norm(inst.definition.card_type) not in type_filter:
        return False
    return True


def _collect_requirement_cards(engine: "GameEngine", owner_idx: int, requirement: dict) -> list[str]:
    owner_key = _norm(str(requirement.get("owner", "me")))
    if owner_key in {"opponent", "enemy", "other"}:
        owners = [1 - owner_idx]
    elif owner_key in {"any", "both", "all", "either"}:
        owners = [owner_idx, 1 - owner_idx]
    else:
        owners = [owner_idx]

    zones = list(requirement.get("zones", []) or [])
    if not zones:
        zones = [str(requirement.get("zone", "field"))]
    card_filter = dict(requirement.get("card_filter", {}) or {})

    out: list[str] = []
    for real_owner in owners:
        for zone_name in zones:
            for uid in _zone_uids_for_owner(engine, real_owner, str(zone_name)):
                if _match_requirement_filter(engine, uid, card_filter):
                    out.append(uid)
    return list(dict.fromkeys(out))


def _consume_scripted_play_costs(engine: "GameEngine", player_idx: int, card: "CardInstance") -> ActionResult | None:
    script = runtime_cards.get_script(card.definition.name)
    if script is None:
        return None
    requirement_cfg = script.play_requirements.get("can_play_by_sacrificing")
    if isinstance(requirement_cfg, dict):
        count = max(1, int(requirement_cfg.get("count", 1) or 1))
        candidates = _collect_requirement_cards(engine, player_idx, requirement_cfg)
        if len(candidates) < count:
            return ActionResult(False, f"Per giocare {card.definition.name} non ci sono abbastanza carte da sacrificare.")
        for uid in candidates[:count]:
            owner = engine.state.instances[uid].owner
            engine.send_to_graveyard(owner, uid)
        return None

    legacy_requirement = str(script.play_requirements.get("can_play_by_sacrificing_specific_card_from_field", "")).strip()
    if legacy_requirement:
        sacrifice_uid = _find_owned_field_uid_by_name(engine, player_idx, legacy_requirement)
        if not sacrifice_uid:
            return ActionResult(False, f"Per giocare {card.definition.name} devi sacrificare {legacy_requirement} dal tuo campo.")
        engine.send_to_graveyard(player_idx, sacrifice_uid)
    return None


# Computes the final Inspiration cost after all card-specific modifiers.
def calculate_play_cost(engine: "GameEngine", player_idx: int, hand_index: int, card: "CardInstance") -> int:
    player = engine.state.players[player_idx]
    ctype = _norm(card.definition.card_type)
    cost = card.definition.faith or 0
    name_key = _norm(card.definition.name)

    if ctype in SAINT_TYPES:
        if name_key == _norm("Atum"):
            cost = 0
        if name_key == _norm("Ra"):
            if any(_norm(engine.state.instances[s_uid].definition.name) == _norm("Nun") for s_uid in engine.all_saints_on_field(player_idx)):
                cost = 0
        if name_key == _norm("Impostore") and not engine.all_saints_on_field(player_idx):
            cost = 0
        if name_key == _norm("Geb"):
            has_building_in_hand = any(
                _norm(engine.state.instances[h_uid].definition.card_type) == "edificio"
                for i, h_uid in enumerate(player.hand)
                if i != hand_index
            )
            if has_building_in_hand:
                cost = max(0, cost - 1)
        atum_on_field = any(
            _norm(engine.state.instances[s_uid].definition.name) == _norm("Atum")
            for s_uid in engine.all_saints_on_field(player_idx)
        )
        if atum_on_field and name_key != _norm("Atum"):
            cost = max(0, (cost + 1) // 2)

    double_turns = engine.state.flags.setdefault("double_cost_turns", {"0": 0, "1": 0})
    if int(double_turns.get(str(player_idx), 0)) > 0:
        cost *= 2
    if engine._has_building(1 - player_idx, "Sfinge"):
        cost *= 2
    return cost


# Applies the computed cost using temporary Inspiration before the regular pool.
def spend_inspiration_for_cost(engine: "GameEngine", player_idx: int, cost: int) -> ActionResult | None:
    player = engine.state.players[player_idx]
    available_inspiration = int(player.inspiration) + int(getattr(player, "temporary_inspiration", 0))
    if available_inspiration < cost:
        return ActionResult(False, "Ispirazione insufficiente.")

    temp = int(getattr(player, "temporary_inspiration", 0))
    use_temp = min(temp, cost)
    player.temporary_inspiration = temp - use_temp
    remaining_cost = cost - use_temp
    player.inspiration -= remaining_cost

    spent = engine.state.flags.setdefault("spent_inspiration_turn", {"0": 0, "1": 0})
    spent[str(player_idx)] = int(spent.get(str(player_idx), 0)) + cost
    return None


# Emits the shared play events used by all cards when leaving the hand.
def emit_play_events(engine: "GameEngine", player_idx: int, uid: str, ctype: str, target: str | None) -> None:
    engine._emit_event("on_card_played", player_idx, card=uid, card_type=ctype, target=target)
    if ctype == "benedizione":
        engine._emit_event("on_blessing_played", player_idx, card=uid, target=target)
    elif ctype == "maledizione":
        engine._emit_event("on_curse_played", player_idx, card=uid, target=target)


# Handles saint placement, summon side effects, and enter-the-field bonuses.
def handle_saint_play(
    engine: "GameEngine",
    player_idx: int,
    place_owner_idx: int,
    uid: str,
    zone: str | None,
    slot: int,
) -> ActionResult:
    player = engine.state.players[player_idx]
    card = engine.state.instances[uid]
    sacrificed_faith_for_brigante = 0

    if _norm(card.definition.name) == _norm("Brigante"):
        own_saints = engine.all_saints_on_field(player_idx)
        if own_saints:
            sacr_uid = own_saints[0]
            sacr = engine.state.instances[sacr_uid]
            sacrificed_faith_for_brigante = max(0, sacr.definition.faith or 0)
            sacr.blessed.append("no_sin_on_death")
            engine.destroy_saint_by_uid(engine.state.instances[sacr_uid].owner, sacr_uid, cause="effect")

    if zone == "attack":
        engine.state.players[place_owner_idx].attack[slot] = uid
    elif zone == "defense":
        engine.state.players[place_owner_idx].defense[slot] = uid
    else:
        player.hand.append(uid)
        return ActionResult(False, "Zona non valida per il posizionamento del santo.")

    card.exhausted = False
    if engine._count_pyramids(player_idx) >= 2:
        card.current_faith = (card.current_faith or 0) + max(0, card.definition.faith or 0)
    if _norm(card.definition.name) == _norm("Brigante") and sacrificed_faith_for_brigante > 0:
        card.current_faith = (card.current_faith or 0) + sacrificed_faith_for_brigante
        card.blessed.append("no_sin_on_death")

    zone_label = "Attacco" if zone == "attack" else "Difesa"
    engine.state.log(f"{player.name} posiziona {card.definition.name} in {zone_label} {slot + 1}.")
    engine._emit_event("on_enter_field", player_idx, card=uid, from_zone="hand")
    engine._emit_event("on_summoned_from_hand", player_idx, card=uid)
    if _norm(card.definition.card_type) == "token":
        engine._emit_event("on_token_summoned", player_idx, token=uid, summoner=player_idx)
    else:
        engine._emit_event("on_opponent_saint_enters_field", 1 - player_idx, saint=uid)

    enter_msg = resolve_enter_effect(engine, player_idx, uid)
    if enter_msg:
        engine.state.log(enter_msg)
    engine._refresh_custode_sigilli_bonus(player_idx)
    return ActionResult(True, "Carta giocata.")


# Handles artifact placement, replacement rules, and enter effects.
def handle_artifact_play(engine: "GameEngine", player_idx: int, uid: str) -> ActionResult:
    player = engine.state.players[player_idx]
    card = engine.state.instances[uid]
    blocked = min(ARTIFACT_SLOTS - 1, engine._count_artifact(1 - player_idx, "Gggnag'ljep"))
    usable_slots = list(range(ARTIFACT_SLOTS - blocked))
    slot = next((i for i in usable_slots if player.artifacts[i] is None), None)
    if slot is None:
        slot = usable_slots[-1]
        replaced = player.artifacts[slot]
        if replaced:
            engine.send_to_graveyard(player_idx, replaced)
    player.artifacts[slot] = uid

    engine.state.log(f"{player.name} posiziona Artefatto {card.definition.name}.")
    engine._emit_event("on_enter_field", player_idx, card=uid, from_zone="hand")
    enter_msg = resolve_enter_effect(engine, player_idx, uid)
    if enter_msg:
        engine.state.log(enter_msg)
    return ActionResult(True, "Carta giocata.")


# Handles building placement and its immediate enter effect resolution.
def handle_building_play(engine: "GameEngine", player_idx: int, uid: str) -> ActionResult:
    player = engine.state.players[player_idx]
    card = engine.state.instances[uid]
    player.building = uid
    engine.state.log(f"{player.name} posiziona Edificio {card.definition.name}.")
    engine._emit_event("on_enter_field", player_idx, card=uid, from_zone="hand")
    enter_msg = resolve_enter_effect(engine, player_idx, uid)
    if enter_msg:
        engine.state.log(enter_msg)
    return ActionResult(True, "Carta giocata.")


# Resolves quick cards from hand, including counter-spell cancellation and cleanup.
def resolve_quick_play_from_hand(engine: "GameEngine", player_idx: int, uid: str, target: str | None) -> ActionResult:
    player = engine.state.players[player_idx]
    card = engine.state.instances[uid]
    if engine._consume_counter_spell(player_idx):
        engine.send_to_graveyard(player_idx, uid)
        engine.state.log(f"{player.name} prova a usare {card.definition.name}, ma viene annullata da Barriera Magica.")
        return ActionResult(True, "Attivazione annullata da Barriera Magica.")
    resolved = resolve_card_effect(engine, player_idx, uid, target)
    moved_elsewhere = False
    for owner_idx in (0, 1):
        p = engine.state.players[owner_idx]
        if (
            uid in p.hand
            or uid in p.deck
            or uid in p.white_deck
            or uid in p.graveyard
            or uid in p.excommunicated
            or uid in p.attack
            or uid in p.defense
            or uid in p.artifacts
            or p.building == uid
        ):
            moved_elsewhere = True
            break
    if not moved_elsewhere:
        engine.send_to_graveyard(player_idx, uid)
    engine._cleanup_zero_faith_saints()
    engine.check_win_conditions()
    return ActionResult(True, resolved)


# Plays a card from hand by validating, paying, and dispatching to the correct resolver branch.
def play_card(engine: "GameEngine", player_idx: int, hand_index: int, target: str | None = None) -> ActionResult:
    player = engine.state.players[player_idx]
    if player_idx != engine.state.active_player:
        return ActionResult(False, "Puoi giocare solo nel tuo turno (tranne Benedizioni/Maledizioni in risposta).")

    card = engine.card_from_hand(player_idx, hand_index)
    if card is None:
        return ActionResult(False, "Indice mano non valido.")
    script = runtime_cards.get_script(card.definition.name)

    ctype = _norm(card.definition.card_type)
    can_play, reason = runtime_cards.can_play(
        engine,
        player_idx,
        player.hand[hand_index],
        target=target,
    )
    if not can_play:
        return ActionResult(False, reason or "Non puoi giocare questa carta.")

    is_valid, error_message, place_owner_idx, zone, slot = validate_play_constraints(engine, player_idx, card, target)
    if not is_valid:
        return ActionResult(False, error_message)

    paid_inspiration = 0
    if ctype not in QUICK_TYPES:
        use_all_remaining = bool(
            script is not None and bool(script.play_requirements.get("consume_all_remaining_inspiration", False))
        )
        if use_all_remaining:
            paid_inspiration = int(player.inspiration) + int(getattr(player, "temporary_inspiration", 0))
            spend_error = spend_inspiration_for_cost(engine, player_idx, paid_inspiration)
            if spend_error is not None:
                return spend_error
        else:
            cost = calculate_play_cost(engine, player_idx, hand_index, card)
            paid_inspiration = int(cost)
            spend_error = spend_inspiration_for_cost(engine, player_idx, cost)
            if spend_error is not None:
                return spend_error

    uid = player.hand.pop(hand_index)
    if script is not None and ctype in SAINT_TYPES:
        faith_mult_raw = script.play_requirements.get("set_source_faith_from_paid_inspiration_multiplier")
        if faith_mult_raw is not None:
            try:
                faith_mult = int(faith_mult_raw)
            except (TypeError, ValueError):
                faith_mult = 1
            card.current_faith = max(0, int(paid_inspiration) * max(0, faith_mult))
        if bool(script.play_requirements.get("store_paid_inspiration_on_source", False)):
            card.blessed = [tag for tag in card.blessed if not str(tag).startswith("paid_inspiration_on_summon:")]
            card.blessed.append(f"paid_inspiration_on_summon:{int(paid_inspiration)}")
    scripted_cost_error = _consume_scripted_play_costs(engine, player_idx, card)
    if scripted_cost_error is not None:
        player.hand.insert(hand_index, uid)
        return scripted_cost_error
    emit_play_events(engine, player_idx, uid, ctype, target)

    if ctype in SAINT_TYPES:
        result = handle_saint_play(engine, player_idx, place_owner_idx, uid, zone, slot)
    elif ctype == "artefatto":
        result = handle_artifact_play(engine, player_idx, uid)
    elif ctype == "edificio":
        result = handle_building_play(engine, player_idx, uid)
    elif ctype in QUICK_TYPES:
        return resolve_quick_play_from_hand(engine, player_idx, uid, target)
    else:
        engine.send_to_graveyard(player_idx, uid)
        engine.state.log(f"{player.name} usa {card.definition.name} senza effetto implementato.")
        result = ActionResult(True, "Carta giocata.")

    if not result.ok:
        return result

    engine._cleanup_zero_faith_saints()
    engine.check_win_conditions()
    return result


# Handles out-of-turn quick plays and the Moribondo protection special case.
def quick_play(engine: "GameEngine", player_idx: int, hand_index: int, target: str | None = None) -> ActionResult:
    player = engine.state.players[player_idx]
    card = engine.card_from_hand(player_idx, hand_index)
    if card is None:
        return ActionResult(False, "Indice mano non valido.")
    ctype = _norm(card.definition.card_type)
    is_moribondo = _norm(card.definition.name) == _norm("Moribondo")
    if ctype not in QUICK_TYPES and not is_moribondo:
        return ActionResult(False, "Solo Benedizione/Maledizione (o Moribondo) sono giocabili fuori turno.")
    uid = player.hand.pop(hand_index)
    emit_play_events(engine, player_idx, uid, ctype, target)
    if is_moribondo:
        target_card = engine.resolve_target_saint(player_idx, target)
        if target_card is None:
            own = engine.all_saints_on_field(player_idx)
            target_card = engine.state.instances[own[0]] if own else None
        if target_card is None:
            player.hand.insert(hand_index, uid)
            return ActionResult(False, "Nessun santo valido da proteggere con Moribondo.")
        player.excommunicated.append(uid)
        target_card.blessed.append("moribondo_shield")
        engine._cleanup_zero_faith_saints()
        engine.check_win_conditions()
        return ActionResult(True, f"{player.name} scomunica Moribondo e protegge {target_card.definition.name}.")
    return resolve_quick_play_from_hand(engine, player_idx, uid, target)



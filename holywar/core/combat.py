from __future__ import annotations

import unicodedata
from typing import TYPE_CHECKING

from holywar.core.results import ActionResult
from holywar.core.state import ATTACK_SLOTS, CardInstance
from holywar.effects.runtime import runtime_cards
from holywar.effects.state_flags import ensure_runtime_state, refresh_player_flags, set_phase

if TYPE_CHECKING:
    from holywar.core.engine import GameEngine


def _norm(text: str) -> str:
    value = unicodedata.normalize("NFKD", text)
    value = "".join(ch for ch in value if not unicodedata.combining(ch))
    return value.strip().lower()


# Starts battle-phase bookkeeping when the first attack of the turn is declared.
def start_battle_phase_if_needed(engine: "GameEngine", player_idx: int) -> None:
    runtime_state = ensure_runtime_state(engine)
    if not bool(runtime_state.get("battle_phase_started", False)):
        runtime_state["battle_phase_started"] = True
        set_phase(engine, "battle")
        engine._emit_event("on_battle_phase_start", player_idx, player=player_idx)
        refresh_player_flags(engine)


# Validates the attacker-side rules that can stop combat before damage is assigned.
def validate_attack_preconditions(
    engine: "GameEngine",
    player_idx: int,
    defender_idx: int,
    attacker: CardInstance,
) -> ActionResult | None:
    attacker_player = engine.state.players[player_idx]
    attacker_name_key = _norm(attacker.definition.name)

    if engine._has_artifact(defender_idx, "Geroglifici"):
        cv = attacker.definition.crosses
        try:
            cv_int = int(float(cv)) if cv is not None else None
        except ValueError:
            cv_int = None
        if cv_int is not None and cv_int <= 2:
            return ActionResult(False, "Geroglifici impedisce l'attacco ai santi con croci <= 2.")
    if attacker_name_key == _norm("Giorno 5: Creature del Mare") and attacker_player.inspiration <= 2:
        return ActionResult(False, "Giorno 5 puo attaccare solo con Ispirazione rimanente > 2.")
    if attacker_name_key == _norm("Giorno 6: Creature di Terra") and attacker_player.inspiration >= 5:
        return ActionResult(False, "Giorno 6 puo attaccare solo con Ispirazione rimanente < 5.")
    if not runtime_cards.get_can_attack(attacker.definition.name):
        return ActionResult(False, f"{attacker.definition.name} non puo attaccare.")
    if engine._is_attacker_blocked_this_turn(attacker):
        return ActionResult(False, f"{attacker.definition.name} non puo attaccare in questo turno.")
    if attacker.exhausted:
        return ActionResult(False, "Questo Santo ha gia attaccato nel turno corrente.")

    attack_count = engine.state.flags.setdefault("attack_count", {"0": 0, "1": 0})
    if (engine._has_artifact(player_idx, "Sabbie Mobili") or engine._has_artifact(defender_idx, "Sabbie Mobili")) and int(
        attack_count.get(str(player_idx), 0)
    ) >= 1:
        return ActionResult(False, "Con Sabbie Mobili attiva puoi attaccare con un solo Santo per turno.")
    return None


# Marks the attacker as committed and updates the per-turn attack counter.
def mark_attack_committed(engine: "GameEngine", player_idx: int, attacker: CardInstance) -> None:
    attacker.exhausted = True
    attack_count = engine.state.flags.setdefault("attack_count", {"0": 0, "1": 0})
    attack_count[str(player_idx)] = int(attack_count.get(str(player_idx), 0)) + 1


# Applies the post-combat building retaliation used by Fiamma Primordiale.
def apply_fiamma_primordiale_after_attack(
    engine: "GameEngine",
    attacker_idx: int,
    defender_idx: int,
    attacker_uid: str,
) -> None:
    if not engine._has_building(defender_idx, "Fiamma Primordiale"):
        return
    if attacker_uid not in engine.state.instances:
        return
    attacker_player = engine.state.players[attacker_idx]
    if attacker_uid not in (attacker_player.attack + attacker_player.defense):
        return
    attacker = engine.state.instances[attacker_uid]
    burn = 2 * (2 ** engine._count_artifact(defender_idx, "Incendio"))
    burn = engine._apply_damage_mitigation(attacker_idx, burn, target_uid=attacker_uid)
    if burn <= 0 or (attacker.current_faith or 0) <= 0:
        return
    before = attacker.current_faith or 0
    attacker.current_faith = max(0, (attacker.current_faith or 0) - burn)
    after = attacker.current_faith or 0
    engine.state.log(
        f"{attacker.definition.name} subisce {burn} danni da Fiamma Primordiale (post-combattimento) (Fede {before}->{after})."
    )
    if (attacker.current_faith or 0) <= 0:
        engine.destroy_saint_by_uid(engine.state.instances[attacker_uid].owner, attacker_uid, cause="effect")
        engine.reduce_sin(defender_idx, 2)


# Resolves the direct-attack case when the defender has no saints on the board.
def resolve_direct_attack(
    engine: "GameEngine",
    player_idx: int,
    defender_idx: int,
    attacker_uid: str,
    attacker: CardInstance,
) -> ActionResult:
    attacker_player = engine.state.players[player_idx]
    defender_player = engine.state.players[defender_idx]
    attacker_name_key = _norm(attacker.definition.name)

    mark_attack_committed(engine, player_idx, attacker)
    if engine._consume_attack_shield(defender_idx):
        engine.state.log(f"{defender_player.name} annulla il primo attacco ricevuto in questo turno.")
        return ActionResult(True, "Attacco annullato da effetto di scudo.")
    base_strength = max(0, attacker.definition.strength or 0)
    damage = engine.get_effective_strength(attacker_uid)
    defender_player.sin += damage
    engine._emit_event(
        "on_this_card_deals_damage",
        player_idx,
        card=attacker_uid,
        target_player=defender_idx,
        amount=damage,
    )
    engine.state.log(
        f"{attacker_player.name} attacca con {attacker.definition.name} direttamente {defender_player.name} "
        f"(Forza base {base_strength}, effettiva {damage}) (+{damage} Peccato)."
    )
    apply_fiamma_primordiale_after_attack(engine, player_idx, defender_idx, attacker_uid)
    engine.check_win_conditions()
    return ActionResult(True, f"Attacco diretto riuscito: +{damage} Peccato all'avversario.")


# Resolves a targeted combat, including barriers, lethal damage, and retaliation rules.
def resolve_targeted_attack(
    engine: "GameEngine",
    player_idx: int,
    defender_idx: int,
    attacker_uid: str,
    attacker: CardInstance,
    target_slot: int | None,
) -> ActionResult:
    attacker_player = engine.state.players[player_idx]
    defender_player = engine.state.players[defender_idx]
    attacker_name_key = _norm(attacker.definition.name)

    if target_slot is None or not (0 <= target_slot < ATTACK_SLOTS):
        return ActionResult(False, "Indica bersaglio valido t1..t3.")
    set_slot = next(
        (
            i
            for i, s_uid in enumerate(defender_player.attack)
            if s_uid and _norm(engine.state.instances[s_uid].definition.name) == _norm("Set")
        ),
        None,
    )
    if set_slot is not None and target_slot != set_slot:
        return ActionResult(False, "Finche Set e in campo, deve essere l'unico bersaglio attaccabile.")
    defender_uid = defender_player.attack[target_slot]
    if defender_uid is None:
        return ActionResult(False, "Nessun Santo avversario nel bersaglio scelto.")
    defender_name = engine.state.instances[defender_uid].definition.name
    if runtime_cards.get_attack_targeting_mode(defender_name) == "untargetable":
        return ActionResult(False, f"{defender_name} non puo essere bersagliato dagli attacchi.")
    if runtime_cards.get_attack_targeting_mode(defender_name) == "only_if_no_other_attackers":
        others = [u for i, u in enumerate(defender_player.attack) if i != target_slot and u is not None]
        if others:
            return ActionResult(False, f"{defender_name} puo essere bersagliato solo se non ci sono altri santi in attacco.")

    mark_attack_committed(engine, player_idx, attacker)
    if engine._consume_attack_shield(defender_idx):
        engine.state.log(f"{defender_player.name} annulla il primo attacco ricevuto in questo turno.")
        return ActionResult(True, "Attacco annullato da effetto di scudo.")
    defender = engine.state.instances[defender_uid]
    barrier = engine._consume_barrier(defender)
    if barrier:
        engine.state.log(f"{defender.definition.name} blocca l'attacco grazie a {barrier}.")
        apply_fiamma_primordiale_after_attack(engine, player_idx, defender_idx, attacker_uid)
        return ActionResult(True, "Attacco annullato da barriera.")

    base_strength = max(0, attacker.definition.strength or 0)
    damage = engine.get_effective_strength(attacker_uid)
    attacker_type_key = _norm(attacker.definition.card_type)
    defender_damage_divisor = 1
    if attacker_type_key in {"santo", "token"}:
        for uid in defender_player.attack + defender_player.defense:
            if not uid:
                continue
            aura_divisor = runtime_cards.get_incoming_damage_from_enemy_saints_divisor(
                engine.state.instances[uid].definition.name
            )
            if aura_divisor > defender_damage_divisor:
                defender_damage_divisor = aura_divisor
    if defender_damage_divisor > 1:
        before_damage = damage
        damage = max(0, damage // defender_damage_divisor)
        engine.state.log(
            f"Mitigazione runtime del danno da Santi: {before_damage}->{damage} (divisore {defender_damage_divisor})."
        )
    damage = engine._apply_damage_mitigation(defender_idx, damage, target_uid=defender_uid)
    def_faith = defender.current_faith or 0
    if damage <= 0:
        engine.state.log(
            f"{attacker_player.name} attacca con {attacker.definition.name} contro {defender.definition.name}, ma non infligge danni."
        )
        return ActionResult(True, "Nessun danno inflitto.")

    before_def = def_faith
    defender.current_faith = max(0, def_faith - damage)
    engine._emit_event(
        "on_this_card_deals_damage",
        player_idx,
        card=attacker_uid,
        target=defender_uid,
        amount=damage,
    )
    engine._emit_event(
        "on_this_card_receives_damage",
        defender_idx,
        card=defender_uid,
        source=attacker_uid,
        amount=damage,
    )
    after_def = defender.current_faith or 0
    engine.state.log(
        f"{attacker_player.name} attacca con {attacker.definition.name} contro {defender.definition.name} "
        f"(Forza base {base_strength}, effettiva {damage}) e infligge {damage} danni (Fede {before_def}->{after_def})."
    )
    lethal = (defender.current_faith or 0) <= 0
    if lethal:
        excommunicate = runtime_cards.get_battle_excommunicate_on_lethal(attacker.definition.name)
        engine.destroy_saint_by_uid(
            engine.state.instances[defender_uid].owner,
            defender_uid,
            excommunicate=excommunicate,
            cause="battle",
        )
        engine._emit_event("on_this_card_kills_in_battle", player_idx, card=attacker_uid, victim=defender_uid)
        if attacker_name_key == _norm("Golem di Pietra"):
            attacker.current_faith = 4
        gain = runtime_cards.get_strength_gain_on_lethal_to_enemy_saint(attacker.definition.name)
        if gain:
            attacker.definition.strength = (attacker.definition.strength or 0) + int(gain)
    else:
        gain = runtime_cards.get_strength_gain_on_damage_to_enemy_saint(attacker.definition.name)
        if gain:
            attacker.definition.strength = (attacker.definition.strength or 0) + int(gain)
        if _norm(defender.definition.name) == _norm("Schiavi") and damage > 0:
            defender.current_faith = (defender.current_faith or 0) + 2

    forced_destroy: list[tuple[int, str]] = []
    attacker_on_board = attacker_uid in (attacker_player.attack + attacker_player.defense)
    defender_on_board = defender_uid in (defender_player.attack + defender_player.defense)
    if runtime_cards.get_post_battle_forced_destroy(attacker.definition.name) and attacker_on_board:
        forced_destroy.append((player_idx, attacker_uid))
        if defender_on_board:
            forced_destroy.append((defender_idx, defender_uid))
    if runtime_cards.get_post_battle_forced_destroy(defender.definition.name) and defender_on_board:
        forced_destroy.append((defender_idx, defender_uid))
        if attacker_on_board:
            forced_destroy.append((player_idx, attacker_uid))
    for owner_idx, forced_uid in forced_destroy:
        if forced_uid not in (engine.state.players[owner_idx].attack + engine.state.players[owner_idx].defense):
            continue
        faith_val = max(0, engine.state.instances[forced_uid].definition.faith or 0)
        engine.destroy_saint_by_uid(engine.state.instances[forced_uid].owner, forced_uid, cause="effect")
        engine.gain_sin(0, faith_val)
        engine.gain_sin(1, faith_val)

    apply_fiamma_primordiale_after_attack(engine, player_idx, defender_idx, attacker_uid)
    engine.check_win_conditions()
    return ActionResult(True, f"Danno inflitto: {damage}.")


# Declares an attack, routes it to the correct combat branch, and preserves all battle checks.
def attack(engine: "GameEngine", player_idx: int, from_slot: int, target_slot: int | None) -> ActionResult:
    if engine.state.phase == "preparation":
        return ActionResult(False, "Durante il turno di preparazione non si puo attaccare.")
    if int(engine.state.flags.get("no_attacks_turn", -1)) == int(engine.state.turn_number):
        return ActionResult(False, "In questo turno gli attacchi sono bloccati da un effetto.")
    if player_idx != engine.state.active_player:
        return ActionResult(False, "Puoi attaccare solo nel tuo turno.")

    start_battle_phase_if_needed(engine, player_idx)
    attacker_player = engine.state.players[player_idx]
    defender_idx = 1 - player_idx
    defender_player = engine.state.players[defender_idx]
    if not (0 <= from_slot < ATTACK_SLOTS):
        return ActionResult(False, "Slot attacco non valido.")
    attacker_uid = attacker_player.attack[from_slot]
    if attacker_uid is None:
        return ActionResult(False, "Nessun Santo in quello slot.")

    attacker = engine.state.instances[attacker_uid]
    engine._emit_event(
        "on_attack_declared",
        player_idx,
        attacker=attacker_uid,
        card=attacker_uid,
        target_slot=target_slot,
    )
    engine._emit_event("on_this_card_attacks", player_idx, card=attacker_uid, target_slot=target_slot)

    validation_error = validate_attack_preconditions(engine, player_idx, defender_idx, attacker)
    if validation_error is not None:
        return validation_error

    if all(slot is None for slot in defender_player.attack + defender_player.defense):
        return resolve_direct_attack(engine, player_idx, defender_idx, attacker_uid, attacker)
    return resolve_targeted_attack(engine, player_idx, defender_idx, attacker_uid, attacker, target_slot)

from __future__ import annotations

import random
import unicodedata
from pathlib import Path

from holywar.core import card_play as card_play_ops
from holywar.core import combat as combat_ops
from holywar.core import destruction as destruction_ops
from holywar.core import query_helpers as query_ops
from holywar.core import turn_flow as turn_flow_ops
from holywar.core import zones as zone_ops
from holywar.core.results import ActionResult
from holywar.core.state import ATTACK_SLOTS, CardInstance, GameState, PlayerState
from holywar.data.deck_builder import build_premade_deck, build_test_deck
from holywar.data.models import CardDefinition
from holywar.effects.library import resolve_activated_effect
from holywar.effects.runtime import runtime_cards
from holywar.effects.state_flags import ensure_runtime_state, refresh_player_flags
from holywar.scripting_api import RuleAPI


# Normalizes text so card comparisons stay accent-insensitive and consistent.
def _norm(text: str) -> str:
    value = unicodedata.normalize("NFKD", text)
    value = "".join(ch for ch in value if not unicodedata.combining(ch))
    return value.strip().lower()


class GameEngine:
    # Initializes the engine with a game state and runtime bookkeeping.
    def __init__(self, state: GameState, seed: int | None = None):
        self.state = state
        self.rng = random.Random(seed)
        self._bootstrap_runtime_bindings()
        ensure_runtime_state(self)
        refresh_player_flags(self)

    # Rebinds runtime triggers for every permanent already present in the match state.
    def _bootstrap_runtime_bindings(self) -> None:
        runtime_cards.ensure_all_cards_migrated(self)
        for controller_idx in (0, 1):
            player = self.state.players[controller_idx]
            for uid in player.attack + player.defense + player.artifacts:
                if uid is not None:
                    runtime_cards.on_enter_bind_triggers(self, controller_idx, uid)
            if player.building is not None:
                runtime_cards.on_enter_bind_triggers(self, controller_idx, player.building)

    # Builds the scripting API wrapper for the selected controller.
    def rules_api(self, controller_idx: int) -> RuleAPI:
        return RuleAPI(self, controller_idx)

    # Clears temporary runtime state when a card leaves the field.
    def _reset_card_runtime_state(self, uid: str) -> None:
        if uid not in self.state.instances:
            return
        inst = self.state.instances[uid]

        # Restore the printed Faith value when the card leaves the field.
        inst.current_faith = inst.definition.faith if inst.definition.faith is not None else None

        # Clear temporary buffs, debuffs, and runtime-only markers.
        inst.blessed = []
        inst.cursed = []

        # Cards outside the field should not keep per-turn usage state.
        inst.exhausted = False

    # Dispatches a gameplay event to the scripting runtime and aliases.
    def _emit_event(self, event: str, actor_idx: int, **payload) -> None:
        self.rules_api(actor_idx).emit(event, actor_idx=actor_idx, **payload)
        # Alias English/Italian spellings used by scripted effects.
        if "relicario" in event:
            self.rules_api(actor_idx).emit(event.replace("relicario", "reliquiary"), actor_idx=actor_idx, **payload)
        elif "reliquiary" in event:
            self.rules_api(actor_idx).emit(event.replace("reliquiary", "relicario"), actor_idx=actor_idx, **payload)

    # Returns the current zone string for a card uid owned by a player.
    def _locate_uid_zone(self, owner_idx: int, uid: str) -> str:
        return zone_ops.locate_uid_zone(self, owner_idx, uid)

    # Builds a brand-new game state, decks, and initial hands.
    @staticmethod
    def create_new(
        cards: list[CardDefinition],
        p1_name: str,
        p2_name: str,
        p1_expansion: str,
        p2_expansion: str,
        p1_premade_deck_id: str | None = None,
        p2_premade_deck_id: str | None = None,
        seed: int | None = None,
    ) -> "GameEngine":
        rng = random.Random(seed)
        instance_counter = 0
        instances: dict[str, CardInstance] = {}

        # Generates unique runtime ids for every card instance created for the match.
        def make_uid() -> str:
            nonlocal instance_counter
            instance_counter += 1
            return f"c{instance_counter:05d}"

        # Clones a card definition into a mutable in-match card instance.
        def copy_card(card_def: CardDefinition, owner: int) -> str:
            uid = make_uid()
            card_copy = CardDefinition.from_dict(card_def.to_dict())
            faith_value = card_copy.faith if card_copy.faith is not None else None
            instances[uid] = CardInstance(
                uid=uid,
                definition=card_copy,
                owner=owner,
                current_faith=faith_value,
            )
            return uid

        deck_warnings: list[str] = []

        # Builds and shuffles the main deck and white deck for one player.
        def build_decks(owner: int, expansion: str, premade_deck_id: str | None) -> tuple[list[str], list[str]]:
            if premade_deck_id:
                premade = build_premade_deck(cards, premade_deck_id)
                built = premade.deck
                deck_warnings.extend(premade.warnings)
            else:
                built = build_test_deck(cards, expansion)
            deck: list[str] = []
            white: list[str] = []
            for cdef in built.main_deck:
                deck.append(copy_card(cdef, owner))
            for cdef in built.white_deck:
                white.append(copy_card(cdef, owner))
            rng.shuffle(deck)
            rng.shuffle(white)
            return deck, white

        p1_deck, p1_white = build_decks(0, p1_expansion, p1_premade_deck_id)
        p2_deck, p2_white = build_decks(1, p2_expansion, p2_premade_deck_id)

        p1 = PlayerState.empty(p1_name)
        p1.deck = p1_deck
        p1.white_deck = p1_white
        p2 = PlayerState.empty(p2_name)
        p2.deck = p2_deck
        p2.white_deck = p2_white
        state = GameState(
            players=[p1, p2],
            instances=instances,
            active_player=0,
            turn_number=0,
            phase="preparation",
            preparation_turns_done=0,
            flags={
                "attack_count": {"0": 0, "1": 0},
                "spore_pending": {"0": False, "1": False},
                "double_cost_turns": {"0": 0, "1": 0},
                "saga_bonus": {"0": 0, "1": 0},
                "activated_turn": {},
                "attack_shield_turn": {},
                "spent_inspiration_turn": {"0": 0, "1": 0},
                "bonus_inspiration_next_turn": {"0": 0, "1": 0},
                "counter_spell_ready": {"0": 0, "1": 0},
                "cards_drawn_this_turn": {"0": [], "1": []},
            },
        )
        engine = GameEngine(state, seed=seed)
        runtime_cards.ensure_all_cards_migrated(engine)
        engine.initial_setup_draw()
        for w in deck_warnings:
            engine.state.log(f"[WARN DECK] {w}")
        return engine

    # Draws the starting hands at the beginning of a new match.
    def initial_setup_draw(self) -> None:
        turn_flow_ops.initial_setup_draw(self)

    # Draws up to the requested number of cards for the selected player.
    def draw_cards(self, player_idx: int, amount: int) -> int:
        return turn_flow_ops.draw_cards(self, player_idx, amount)

    # Plays a card from hand through the main gameplay entry point.
    def play_card(self, player_idx: int, hand_index: int, target: str | None = None) -> ActionResult:
        return card_play_ops.play_card(self, player_idx, hand_index, target)

    # Returns every saint or token the player currently controls on the field.
    def all_saints_on_field(self, player_idx: int) -> list[str]:
        return query_ops.all_saints_on_field(self, player_idx)

    # Returns only the saints or tokens currently in the player's attack row.
    def all_attack_saints(self, player_idx: int) -> list[str]:
        return query_ops.all_attack_saints(self, player_idx)

    # Checks whether the player controls a named artifact.
    def _has_artifact(self, player_idx: int, name: str) -> bool:
        return query_ops.has_artifact(self, player_idx, name)

    # Counts how many copies of a named artifact the player controls.
    def _count_artifact(self, player_idx: int, name: str) -> int:
        return query_ops.count_artifact(self, player_idx, name)

    # Checks whether the player controls a named building.
    def _has_building(self, player_idx: int, name: str) -> bool:
        return query_ops.has_building(self, player_idx, name)

    # Counts the pyramid artifacts currently on the player's field.
    def _count_pyramids(self, player_idx: int) -> int:
        return query_ops.count_pyramids(self, player_idx)

    # Removes any saints that have reached zero Faith after an effect resolves.
    def _cleanup_zero_faith_saints(self) -> None:
        destruction_ops.cleanup_zero_faith_saints(self)

    # Finds which player currently owns the board slot containing a uid.
    def _find_board_owner_of_uid(self, uid: str) -> int | None:
        return zone_ops.find_board_owner_of_uid(self, uid)

    # Reads the seal count currently stored on Altare dei Sette Sigilli.
    def _get_altare_sigilli(self, player_idx: int) -> int:
        return query_ops.get_altare_sigilli(self, player_idx)

    # Updates the seal count stored on Altare dei Sette Sigilli.
    def _set_altare_sigilli(self, player_idx: int, value: int) -> None:
        query_ops.set_altare_sigilli(self, player_idx, value)

    # Recomputes the Custode dei Sigilli bonus from the current seal count.
    def _refresh_custode_sigilli_bonus(self, player_idx: int) -> None:
        query_ops.refresh_custode_sigilli_bonus(self, player_idx)

    # Computes the final combat strength of a card after all bonuses and penalties.
    def get_effective_strength(self, uid: str) -> int:
        inst = self.state.instances[uid]
        owner = inst.owner
        opponent = 1 - owner
        strength = max(0, inst.definition.strength or 0)
        for tag in inst.blessed:
            if tag.startswith("buff_str:"):
                try:
                    strength += int(tag.split(":", 1)[1])
                except ValueError:
                    pass
        if self._has_artifact(owner, "Járngreipr"):
            strength += 2
        if self._has_artifact(owner, "Gungnir"):
            strength += 1
        for rule in runtime_cards.get_strength_bonus_rules(inst.definition.name):
            artifact_name = str(rule.get("artifact_name", "")).strip()
            if not artifact_name or not self._has_artifact(owner, artifact_name):
                continue
            required_name = str(rule.get("if_card_name", "")).strip()
            if required_name and _norm(inst.definition.name) != _norm(required_name):
                continue
            strength += int(rule.get("self_bonus", 0) or 0)
        if self._count_pyramids(owner) >= 1:
            strength += 5
        sigilli_threshold = runtime_cards.get_sigilli_strength_bonus_threshold(inst.definition.name)
        sigilli_amount = runtime_cards.get_sigilli_strength_bonus_amount(inst.definition.name)
        if sigilli_threshold is not None and sigilli_amount is not None and self._get_altare_sigilli(owner) >= int(sigilli_threshold):
            strength += int(sigilli_amount)
        if self._has_artifact(opponent, "Segno Del Passato"):
            strength -= 4
        return max(0, strength)

    # Adds Sin to a player and refreshes any derived runtime flags.
    def gain_sin(self, player_idx: int, amount: int) -> None:
        if amount <= 0:
            return
        self.state.players[player_idx].sin += amount
        refresh_player_flags(self)

    # Removes Sin from a player without letting the total go below zero.
    def reduce_sin(self, player_idx: int, amount: int) -> None:
        if amount <= 0:
            return
        p = self.state.players[player_idx]
        p.sin = max(0, p.sin - amount)
        refresh_player_flags(self)

    # Destroys a saint or token by uid using the shared destruction flow.
    def destroy_saint_by_uid(
        self, owner_idx: int, uid: str, excommunicate: bool = False, cause: str = "effect"
    ) -> None:
        destruction_ops.destroy_saint_by_uid(self, owner_idx, uid, excommunicate=excommunicate, cause=cause)

    # Starts the active player's turn and applies all start-of-turn effects.
    def start_turn(self) -> None:
        turn_flow_ops.start_turn(self)

    # Ends the current turn and advances control to the next player.
    def end_turn(self) -> None:
        turn_flow_ops.end_turn(self)

    # Returns the card instance currently stored in a hand slot.
    def card_from_hand(self, player_idx: int, hand_index: int) -> CardInstance | None:
        player = self.state.players[player_idx]
        if hand_index < 0 or hand_index >= len(player.hand):
            return None
        return self.state.instances[player.hand[hand_index]]

    # Validates whether the card can be played in the requested zone and context.
    # Kept on the engine as a delegation layer while the logic now lives in the card-play module.
    def _validate_play_constraints(
        self,
        player_idx: int,
        card: CardInstance,
        target: str | None,
    ) -> tuple[bool, str, int, str | None, int]:
        return card_play_ops.validate_play_constraints(self, player_idx, card, target)

    # Computes the final Inspiration cost after all card-specific modifiers.
    # Kept on the engine to preserve the public API while the logic is delegated.
    def _calculate_play_cost(self, player_idx: int, hand_index: int, card: CardInstance) -> int:
        return card_play_ops.calculate_play_cost(self, player_idx, hand_index, card)

    # Applies the computed cost using temporary Inspiration before the regular pool.
    # Kept on the engine as a thin wrapper around the dedicated card-play module.
    def _spend_inspiration_for_cost(self, player_idx: int, cost: int) -> ActionResult | None:
        return card_play_ops.spend_inspiration_for_cost(self, player_idx, cost)

    # Emits the shared play events that every card uses when leaving the hand.
    # Kept on the engine so existing callers can continue using the same method name.
    def _emit_play_events(self, player_idx: int, uid: str, ctype: str, target: str | None) -> None:
        card_play_ops.emit_play_events(self, player_idx, uid, ctype, target)

    # Handles saint placement, summon side effects, and enter-the-field bonuses.
    # Kept on the engine as a delegation layer while the detailed logic lives elsewhere.
    def _handle_saint_play(
        self,
        player_idx: int,
        place_owner_idx: int,
        uid: str,
        zone: str | None,
        slot: int,
    ) -> ActionResult:
        return card_play_ops.handle_saint_play(self, player_idx, place_owner_idx, uid, zone, slot)

    # Handles artifact placement, replacement rules, and enter effects.
    # Kept on the engine to preserve compatibility while delegating the implementation.
    def _handle_artifact_play(self, player_idx: int, uid: str) -> ActionResult:
        return card_play_ops.handle_artifact_play(self, player_idx, uid)

    # Handles building placement and its immediate enter effect resolution.
    # Kept on the engine as a stable entry point with delegated logic.
    def _handle_building_play(self, player_idx: int, uid: str) -> ActionResult:
        return card_play_ops.handle_building_play(self, player_idx, uid)

    # Resolves quick cards from hand, including counter-spell cancellation and cleanup.
    # Kept on the engine so reactive-play callers do not need to change.
    def _resolve_quick_play_from_hand(self, player_idx: int, uid: str, target: str | None) -> ActionResult:
        return card_play_ops.resolve_quick_play_from_hand(self, player_idx, uid, target)

    # Activates the ability of a card already present on the board.
    def activate_ability(self, player_idx: int, source: str, target: str | None = None) -> ActionResult:
        if player_idx != self.state.active_player:
            return ActionResult(False, "Puoi attivare abilita solo nel tuo turno.")
        uid = self.resolve_board_uid(player_idx, source)
        if uid is None:
            return ActionResult(False, "Sorgente non valida. Usa a1..a3, d1..d3, r1..r4 o b.")
        if "silenced" in self.state.instances[uid].cursed:
            return ActionResult(False, "Questa carta ha i suoi effetti annullati.")
        msg = resolve_activated_effect(self, player_idx, uid, target)
        self._cleanup_zero_faith_saints()
        self.check_win_conditions()
        return ActionResult(True, msg)

    # Checks whether a card has already used its once-per-turn activation.
    def can_activate_once_per_turn(self, uid: str) -> bool:
        used = self.state.flags.setdefault("activated_turn", {})
        return int(used.get(uid, -1)) != int(self.state.turn_number)

    # Marks a card as having consumed its activation for the current turn.
    def mark_activated_this_turn(self, uid: str) -> None:
        used = self.state.flags.setdefault("activated_turn", {})
        used[uid] = int(self.state.turn_number)

    # Resolves a reactive blessing, curse, or special quick-play card.
    def quick_play(self, player_idx: int, hand_index: int, target: str | None = None) -> ActionResult:
        return card_play_ops.quick_play(self, player_idx, hand_index, target)

    # Swaps two saints within the active player's attack row.
    def move_attack_positions(self, player_idx: int, from_slot: int, to_slot: int) -> ActionResult:
        if player_idx != self.state.active_player:
            return ActionResult(False, "Movimento disponibile solo nel tuo turno.")
        player = self.state.players[player_idx]
        if not (0 <= from_slot < ATTACK_SLOTS and 0 <= to_slot < ATTACK_SLOTS):
            return ActionResult(False, "Slot non valido.")
        player.attack[from_slot], player.attack[to_slot] = player.attack[to_slot], player.attack[from_slot]
        return ActionResult(True, "Santi in attacco scambiati.")

    # Starts battle-phase bookkeeping when the first attack of the turn is declared.
    def _start_battle_phase_if_needed(self, player_idx: int) -> None:
        combat_ops.start_battle_phase_if_needed(self, player_idx)

    # Validates the attacker-side rules that can stop combat before damage is assigned.
    def _validate_attack_preconditions(self, player_idx: int, defender_idx: int, attacker: CardInstance) -> ActionResult | None:
        return combat_ops.validate_attack_preconditions(self, player_idx, defender_idx, attacker)

    # Marks the attacker as committed and updates the per-turn attack counter.
    def _mark_attack_committed(self, player_idx: int, attacker: CardInstance) -> None:
        combat_ops.mark_attack_committed(self, player_idx, attacker)

    # Resolves the direct-attack case when the defender has no saints on the board.
    def _resolve_direct_attack(self, player_idx: int, defender_idx: int, attacker_uid: str, attacker: CardInstance) -> ActionResult:
        return combat_ops.resolve_direct_attack(self, player_idx, defender_idx, attacker_uid, attacker)

    # Resolves a targeted combat, including barriers, lethal damage, and retaliation rules.
    def _resolve_targeted_attack(
        self,
        player_idx: int,
        defender_idx: int,
        attacker_uid: str,
        attacker: CardInstance,
        target_slot: int | None,
    ) -> ActionResult:
        return combat_ops.resolve_targeted_attack(self, player_idx, defender_idx, attacker_uid, attacker, target_slot)

    # Declares and resolves an attack through the combat module.
    def attack(self, player_idx: int, from_slot: int, target_slot: int | None) -> ActionResult:
        return combat_ops.attack(self, player_idx, from_slot, target_slot)

    # Destroys the saint occupying a specific attack slot.
    def _kill_saint(self, owner_idx: int, attack_slot: int) -> None:
        player = self.state.players[owner_idx]
        uid = player.attack[attack_slot]
        if uid is None:
            return
        self.destroy_saint_by_uid(self.state.instances[uid].owner, uid, cause="battle")

    # Moves a card into the graveyard using the shared zone-transition rules.
    def send_to_graveyard(
        self,
        owner_idx: int,
        uid: str,
        token_to_white: bool = False,
        from_zone_override: str | None = None,
    ) -> None:
        zone_ops.send_to_graveyard(
            self,
            owner_idx,
            uid,
            token_to_white=token_to_white,
            from_zone_override=from_zone_override,
        )

    # Moves a card into the excommunication zone through the zone module.
    def excommunicate_card(self, owner_idx: int, uid: str, from_zone_override: str | None = None) -> None:
        zone_ops.excommunicate_card(self, owner_idx, uid, from_zone_override=from_zone_override)

    # Moves an absolved card from excommunication back into the graveyard.
    def absolve_card_to_graveyard(self, owner_idx: int, uid: str) -> None:
        zone_ops.absolve_card_to_graveyard(self, owner_idx, uid)

    # Removes a uid from every board slot owned by the given player.
    def _remove_from_board(self, player: PlayerState, uid: str) -> None:
        zone_ops.remove_from_board(self, player, uid)

    # Parses a compact board target like a2 or d1 into zone and slot data.
    def _parse_zone_target(self, target: str | None) -> tuple[str | None, int]:
        return query_ops.parse_zone_target(target)

    # Returns the first available empty slot from a board row.
    def _first_open(self, slots: list[str | None]) -> int | None:
        return query_ops.first_open(slots)

    # Consumes a one-shot barrier blessing when the defender has one.
    def _consume_barrier(self, defender: CardInstance) -> str | None:
        return query_ops.consume_barrier(defender)

    # Applies static damage prevention rules before damage is committed.
    def _apply_damage_mitigation(self, target_owner_idx: int, damage: int) -> int:
        return query_ops.apply_damage_mitigation(self, target_owner_idx, damage)

    # Checks whether a temporary attack lock still prevents this attacker from acting.
    def _is_attacker_blocked_this_turn(self, attacker: CardInstance) -> bool:
        return query_ops.is_attacker_blocked_this_turn(self, attacker)

    # Consumes the defender's once-per-turn attack shield if it is active.
    def _consume_attack_shield(self, defender_idx: int) -> bool:
        return query_ops.consume_attack_shield(self, defender_idx)

    # Consumes a stored counter-spell charge from the opposing player.
    def _consume_counter_spell(self, caster_idx: int) -> bool:
        return query_ops.consume_counter_spell(self, caster_idx)

    # Resolves a board target string into a saint instance.
    def resolve_target_saint(self, player_idx: int, target: str | None) -> CardInstance | None:
        return query_ops.resolve_target_saint(self, player_idx, target)

    # Resolves a board target string into an artifact or building uid.
    def resolve_target_artifact_or_building(self, player_idx: int, target: str | None) -> str | None:
        return query_ops.resolve_target_artifact_or_building(self, player_idx, target)

    # Resolves any supported board source string into the corresponding uid.
    def resolve_board_uid(self, player_idx: int, source: str | None) -> str | None:
        return query_ops.resolve_board_uid(self, player_idx, source)

    # Removes a card from the board without applying any Sin consequences.
    def remove_from_board_no_sin(self, owner_idx: int, uid: str) -> None:
        zone_ops.remove_from_board_no_sin(self, owner_idx, uid)

    # Applies the post-combat burn effect from Fiamma Primordiale.
    def _apply_fiamma_primordiale_after_attack(self, attacker_idx: int, defender_idx: int, attacker_uid: str) -> None:
        combat_ops.apply_fiamma_primordiale_after_attack(self, attacker_idx, defender_idx, attacker_uid)

    # Destroys any card type using the shared destruction logic.
    def destroy_any_card(self, owner_idx: int, uid: str) -> None:
        destruction_ops.destroy_any_card(self, owner_idx, uid)

    # Resolves the recurring Cataclisma Ciclico destruction effect.
    def _apply_cataclisma_ciclico(self, active_idx: int) -> None:
        if not self._has_artifact(active_idx, "Cataclisma Ciclico"):
            return
        own_saints = self.all_saints_on_field(active_idx)
        opp_idx = 1 - active_idx
        opp_saints = self.all_saints_on_field(opp_idx)
        if not own_saints and not opp_saints:
            return
        if opp_saints:
            target_uid = opp_saints[0]
            target_owner = opp_idx
        else:
            target_uid = own_saints[0]
            target_owner = active_idx
        target_name = self.state.instances[target_uid].definition.name
        self.destroy_saint_by_uid(self.state.instances[target_uid].owner, target_uid, cause="effect")
        if target_owner == active_idx:
            self.gain_sin(opp_idx, 2)
            self.state.log(f"Cataclisma Ciclico distrugge {target_name}: +2 Peccato a {self.state.players[opp_idx].name}.")
        else:
            self.reduce_sin(active_idx, 1)
            self.state.log(f"Cataclisma Ciclico distrugge {target_name}: {self.state.players[active_idx].name} perde 1 Peccato.")

    # Finds a matching card by name inside the player's deck.
    def find_card_uid_in_deck(self, player_idx: int, name: str) -> str | None:
        return query_ops.find_card_uid_in_deck(self, player_idx, name)

    # Finds a matching card by name inside the player's graveyard.
    def find_card_uid_in_graveyard(self, player_idx: int, name: str) -> str | None:
        return query_ops.find_card_uid_in_graveyard(self, player_idx, name)

    # Moves a specific deck card into the player's hand if possible.
    def move_deck_card_to_hand(self, player_idx: int, uid: str) -> bool:
        return zone_ops.move_deck_card_to_hand(self, player_idx, uid)

    # Moves a specific graveyard card back into the player's hand.
    def move_graveyard_card_to_hand(self, player_idx: int, uid: str) -> bool:
        return zone_ops.move_graveyard_card_to_hand(self, player_idx, uid)

    # Returns a card from the board to hand while preserving ownership rules.
    def move_board_card_to_hand(self, owner_idx: int, uid: str) -> bool:
        return zone_ops.move_board_card_to_hand(self, owner_idx, uid)

    # Places a graveyard card on the bottom of the deck.
    def move_graveyard_card_to_deck_bottom(self, player_idx: int, uid: str) -> bool:
        return zone_ops.move_graveyard_card_to_deck_bottom(self, player_idx, uid)

    # Clears the per-turn activated-effect usage registry.
    def _reset_effect_usage_this_turn(self) -> None:
        self.state.flags["effect_usage_per_turn"] = {}

    # Removes all once-per-turn markers so the next turn starts cleanly.
    def _reset_turn_once_markers_this_turn(self) -> None:
        marker_prefix = "once_per_turn:"
        for inst in self.state.instances.values():
            keep = [tag for tag in inst.blessed if not tag.startswith(marker_prefix)]
            if len(keep) != len(inst.blessed):
                inst.blessed = keep

    # Places a card uid directly into a specific board zone and slot.
    def place_card_from_uid(self, player_idx: int, uid: str, zone: str, slot: int) -> bool:
        return zone_ops.place_card_from_uid(self, player_idx, uid, zone, slot)

    # Returns the currently empty slot indexes for a board zone.
    def empty_slots(self, player_idx: int, zone: str) -> list[int]:
        return zone_ops.empty_slots(self, player_idx, zone)

    # Lists the expansions represented in the current match state.
    def available_expansions(self) -> list[str]:
        return query_ops.available_expansions(self)

    # Checks whether a player has met one of the match-ending conditions.
    def check_win_conditions(self) -> None:
        for idx, player in enumerate(self.state.players):
            if player.sin >= 100:
                self.state.winner = 1 - idx
                self.state.log(f"{player.name} ha raggiunto 100 Peccato. Vince {self.state.players[self.state.winner].name}.")
                return
            if not player.deck and not player.hand and all(slot is None for slot in player.attack + player.defense):
                self.state.winner = 1 - idx
                self.state.log(f"{player.name} ha esaurito tutte le carte giocabili. Vince {self.state.players[self.state.winner].name}.")
                return

    # Exports the accumulated match log to a text file.
    def export_logs(self, path: str | Path) -> Path:
        out = Path(path)
        out.write_text("\n".join(self.state.logs), encoding="utf-8")
        return out

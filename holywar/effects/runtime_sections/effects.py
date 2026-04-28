from __future__ import annotations

from typing import TYPE_CHECKING, Any, Callable
import json
from pathlib import Path

from holywar.core import state
from holywar.core.state import MAX_HAND, CardInstance
from holywar.effects.card_scripts_loader import iter_card_scripts
from holywar.scripting_api import RuleEventContext
from holywar.data.importer import load_cards_json
from holywar.data.models import CardDefinition
from holywar.effects.runtime import (
    _norm,
    _card_name_haystack,
    _card_name_variants,
    _card_matches_name,
    SUPPORTED_EFFECT_ACTIONS,
    EFFECT_ACTION_ALIASES,
    SUPPORTED_CONDITION_KEYS,
    TriggerSpec,
    CardFilterSpec,
    TargetSpec,
    EffectSpec,
    TriggeredEffectSpec,
    ActionSpec,
    CardScript,
)

if TYPE_CHECKING:
    from holywar.core.engine import GameEngine

# This module defines the `RuntimeEffectsMixin` class, which provides helper methods for resolving targets, moving cards between zones, summoning tokens, and applying effects based on the card scripts defined in the game. The mixin includes methods for handling various target specifications, managing equipment links, and applying specific effect actions such as increasing faith or returning cards to hand. The methods interact with the game engine's state and instances to perform the necessary operations while ensuring that the game rules are respected. This mixin can be used by the main game engine class to implement the core mechanics of card effects during gameplay.
class RuntimeEffectsMixin:
    """Target resolution, zone moves and low-level effect execution helpers."""
    if TYPE_CHECKING:
        _temp_faith: dict[int, dict[str, list[tuple[str, int, str]]]]

        # The following are method signatures for helper methods that are used within the `RuntimeEffectsMixin` class. These methods are responsible for various tasks such as resolving targets based on the current game state, moving cards between zones, managing equipment links, and evaluating conditions for effects. The actual implementations of these methods would contain the logic to interact with the game engine's state and perform the necessary operations according to the rules of the game.
        def _selected_target_raw_for_current_action(self, engine: GameEngine) -> str: ...
        def _selected_target_uid_for_current_action(self, engine: GameEngine, owner_idx: int) -> str | None: ...
        def _collect_selectable_targets_for_manual_target(
            self,
            engine: GameEngine,
            owner_idx: int,
            target: TargetSpec,
        ) -> list[str]: ...
        def _filter_target_pool(
            self,
            engine: GameEngine,
            owner_idx: int,
            target: TargetSpec,
            pool: list[str],
        ) -> list[str]: ...
        def _is_uid_on_field(self, engine: GameEngine, uid: str) -> bool: ...
        def _eval_condition_node(self, ctx: RuleEventContext, owner_idx: int, node: dict[str, Any]) -> bool: ...
        def resolve_enter(self, engine: GameEngine, player_idx: int, uid: str) -> object: ...
        def is_immune_to_action(self, card_name: str, action_name: str) -> bool: ...
        def get_is_altare_sigilli(self, card_name: str) -> bool: ...
        def get_is_pyramid(self, card_name: str) -> bool: ...

    def _has_invert_saint_summon_aura(self, engine: GameEngine) -> bool:
        for p_idx in (0, 1):
            player = engine.state.players[p_idx]
            field_uids = [uid for uid in (player.attack + player.defense + player.artifacts) if uid]
            if player.building:
                field_uids.append(player.building)
            for uid in field_uids:
                inst = engine.state.instances.get(uid)
                if inst is None:
                    continue
                script = self.get_script(inst.definition.name)
                if script and bool(script.inverts_saint_summon_controller):
                    return True
        return False

    def _maybe_auto_activate_discarded_from_hand_by_effect(
        self,
        engine: GameEngine,
        discarded_owner_idx: int,
        discarded_uid: str,
        source_uid: str,
    ) -> None:
        if not source_uid or source_uid == discarded_uid:
            return
        inst = engine.state.instances.get(discarded_uid)
        if inst is None:
            return
        script = self.get_script(inst.definition.name)
        if script is None:
            return
        if not bool(script.play_requirements.get("auto_activate_when_discarded_from_hand_by_effect", False)):
            return
        self.resolve_play(engine, discarded_owner_idx, discarded_uid, None)

    # This method resolves the targets specified by a `TargetSpec` based on the current game state and the owner of the effect. It handles various types of target specifications, such as cards controlled by the owner, event cards, source cards, equipped targets, and selected targets. The method collects potential targets into a pool and then filters them according to the criteria defined in the `TargetSpec`. Finally, it returns a list of resolved target UIDs, limited by the `max_targets` property if specified.
    def _resolve_targets(self, engine: GameEngine, owner_idx: int, target: TargetSpec) -> list[str]:
        pool: list[str] = []
        ttype = _norm(target.type)
        if ttype == "cards_controlled_by_owner":
            zones = [z for z in target.zones if str(z).strip()]
            if not zones:
                zones = [target.zone]
            for scoped_owner in self._target_owner_indices(owner_idx, target.owner):
                p = engine.state.players[scoped_owner]
                for zone_name in zones:
                    zone = _norm(zone_name)
                    if zone == "field":
                        for uid in p.attack + p.defense + p.artifacts:
                            if uid:
                                pool.append(uid)
                        if p.building:
                            pool.append(p.building)
                    elif zone == "hand":
                        pool.extend(p.hand)
                    elif zone in {"deck", "relicario"}:
                        promise_state = dict(engine.state.flags.get("oltretomba_promise_active", {"0": False, "1": False}) or {"0": False, "1": False})
                        merged = bool(promise_state.get(str(scoped_owner), False))
                        if merged:
                            # when merged, include both deck and graveyard
                            pool.extend(p.deck)
                            pool.extend([uid for uid in p.graveyard if uid not in p.deck])
                        else:
                            pool.extend(p.deck)
                    elif zone == "graveyard":
                        promise_state = dict(engine.state.flags.get("oltretomba_promise_active", {"0": False, "1": False}) or {"0": False, "1": False})
                        merged = bool(promise_state.get(str(scoped_owner), False))
                        if merged:
                            pool.extend(p.graveyard)
                            pool.extend([uid for uid in p.deck if uid not in p.graveyard])
                        else:
                            pool.extend(p.graveyard)
                    elif zone == "excommunicated":
                        pool.extend(p.excommunicated)
        elif ttype == "event_card":
            event_uid = str(engine.state.flags.get("_runtime_event_card", ""))
            if event_uid:
                pool.append(event_uid)
        elif ttype == "source_card":
            source_uid = str(engine.state.flags.get("_runtime_source_card", ""))
            if source_uid:
                pool.append(source_uid)
        elif ttype == "event_source_card":
            source_uid = str(engine.state.flags.get("_runtime_event_source", ""))
            if source_uid:
                pool.append(source_uid)
        elif ttype == "equipped_target_of_source":
            source_uid = str(engine.state.flags.get("_runtime_source_card", "")).strip()
            if source_uid:
                equipped_uid = self._equipment_target_uid(engine, source_uid)
                if equipped_uid:
                    pool.append(equipped_uid)
        elif ttype == "selected_target":
            raw_selected = self._selected_target_raw_for_current_action(engine)
            if raw_selected:
                selected = raw_selected.split(",", 1)[0].strip()

                if selected.startswith("buff:"):
                    selected = selected.split(":", 1)[1]

                # If the selected target is directly a UID of an instance, add it to the pool. Otherwise, attempt to resolve it based on the specified syntax and the current game state.
                if selected in engine.state.instances:
                    pool.append(selected)
                else:
                    source_uid = str(engine.state.flags.get("_runtime_source_card", "")).strip()
                    owner_key = _norm(target.owner)
                    allow_any_owner = owner_key in {"any", "both", "all", "either"}
                    owner_candidates = self._target_owner_indices(owner_idx, target.owner)

                    # The following block checks if the selected target includes a side prefix (e.g., "opp:", "self:") and adjusts the owner candidates and the selected token accordingly. This allows for more flexible target specifications where the player can indicate whether they are referring to their own cards or their opponent's cards.
                    if ":" in selected:
                        side, token = selected.split(":", 1)
                        side_key = _norm(side)
                        if side_key in {"o", "opp", "enemy", "opponent", "other"}:
                            owner_candidates = [1 - owner_idx]
                            selected = token.strip()
                        elif side_key in {"s", "self", "me", "own", "owner", "controller"}:
                            owner_candidates = [owner_idx]
                            selected = token.strip()

                    # The following block attempts to resolve the selected target by checking various zones (attack, defense, artifacts, building) for each of the owner candidates. If a matching UID is found in the specified zone, it is added to the pool. If the selected target cannot be resolved through these means, it falls back to checking if the selected token matches any selectable targets based on the current game state and the criteria defined in the `TargetSpec`.
                    resolved = False
                    fallback_uid: str | None = None
                    for real_owner in owner_candidates:
                        p = engine.state.players[real_owner]
                        zone, slot = engine._parse_zone_target(selected)
                        if zone is not None:
                            if zone == "attack" and 0 <= slot < len(p.attack):
                                uid = p.attack[slot]
                                if uid:
                                    if allow_any_owner and uid == source_uid and len(owner_candidates) > 1:
                                        fallback_uid = uid
                                        continue
                                    pool.append(uid)
                                    resolved = True
                                    break
                            elif zone == "defense" and 0 <= slot < len(p.defense):
                                uid = p.defense[slot]
                                if uid:
                                    if allow_any_owner and uid == source_uid and len(owner_candidates) > 1:
                                        fallback_uid = uid
                                        continue
                                    pool.append(uid)
                                    resolved = True
                                    break
                        elif selected.startswith("r") and len(selected) == 2 and selected[1].isdigit():
                            art_idx = int(selected[1]) - 1
                            if 0 <= art_idx < len(p.artifacts):
                                uid = p.artifacts[art_idx]
                                if uid:
                                    if allow_any_owner and uid == source_uid and len(owner_candidates) > 1:
                                        fallback_uid = uid
                                        continue
                                    pool.append(uid)
                                    resolved = True
                                    break
                        elif selected == "b":
                            if p.building:
                                if allow_any_owner and p.building == source_uid and len(owner_candidates) > 1:
                                    fallback_uid = p.building
                                    continue
                                pool.append(p.building)
                                resolved = True
                                break

                    # If the target was not resolved through the specified syntax and zones, but a fallback UID was identified (e.g., when the selected target matches the source card and the specification allows for any owner), add the fallback UID to the pool.
                    if not resolved and fallback_uid:
                        pool.append(fallback_uid)
                        resolved = True

                    # If the target was still not resolved, attempt to match the selected token against selectable targets based on the current game state and the criteria defined in the `TargetSpec`. This allows for more flexible targeting where the player can specify a token that matches certain characteristics of potential targets, rather than relying solely on specific syntax or UIDs.
                    if not resolved:
                        lookup = selected
                        if ":" in lookup:
                            pref, val = lookup.split(":", 1)
                            pref_key = _norm(pref)
                            if pref_key in {"deck", "relicario", "grave", "graveyard", "excom", "excommunicated"}:
                                lookup = val.strip()
                        selectable = self._collect_selectable_targets_for_manual_target(engine, owner_idx, target)
                        for candidate_uid in selectable:
                            if _norm(engine.state.instances[candidate_uid].definition.name) == _norm(lookup):
                                pool.append(candidate_uid)
                                break

        # The following block handles the case where the target type is "selected_targets", which allows for multiple targets to be specified in a comma-separated format. It processes each selected target in the same way as the single "selected_target" case, allowing for flexible targeting based on the current game state and the criteria defined in the `TargetSpec`.
        elif ttype == "selected_targets":
            raw_selected = self._selected_target_raw_for_current_action(engine)
            if raw_selected:
                parts = [part.strip() for part in raw_selected.split(",") if part.strip()]
                source_uid = str(engine.state.flags.get("_runtime_source_card", "")).strip()
                owner_key = _norm(target.owner)
                allow_any_owner = owner_key in {"any", "both", "all", "either"}

                # Process each selected target in the comma-separated list, applying the same resolution logic as for a single selected target. This allows for multiple targets to be specified and resolved in a single action, providing greater flexibility for effects that can affect multiple cards or instances based on player selection.
                for selected in parts:
                    if selected.startswith("buff:"):
                        selected = selected.split(":", 1)[1]

                    if selected in engine.state.instances:
                        pool.append(selected)
                        continue

                    # Check for side prefixes (e.g., "opp:", "self:") to determine owner candidates and adjust the selected token accordingly. This allows for more flexible targeting specifications where the player can indicate whether they are referring to their own cards or their opponent's cards for each selected target.
                    owner_candidates = self._target_owner_indices(owner_idx, target.owner)
                    if ":" in selected:
                        side, token = selected.split(":", 1)
                        side_key = _norm(side)
                        if side_key in {"o", "opp", "enemy", "opponent", "other"}:
                            owner_candidates = [1 - owner_idx]
                            selected = token.strip()
                        elif side_key in {"s", "self", "me", "own", "owner", "controller"}:
                            owner_candidates = [owner_idx]
                            selected = token.strip()

                    # The following block attempts to resolve the selected target by checking various zones (attack, defense, artifacts, building) for each of the owner candidates. If a matching UID is found in the specified zone, it is added to the pool. If the selected target cannot be resolved through these means, it falls back to checking if the selected token matches any selectable targets based on the current game state and the criteria defined in the `TargetSpec`.
                    resolved = False
                    fallback_uid: str | None = None
                    for real_owner in owner_candidates:
                        p = engine.state.players[real_owner]
                        zone, slot = engine._parse_zone_target(selected)
                        if zone is not None:
                            if zone == "attack" and 0 <= slot < len(p.attack):
                                uid = p.attack[slot]
                                if uid:
                                    if allow_any_owner and uid == source_uid and len(owner_candidates) > 1:
                                        fallback_uid = uid
                                        continue
                                    pool.append(uid)
                                    resolved = True
                                    break
                            elif zone == "defense" and 0 <= slot < len(p.defense):
                                uid = p.defense[slot]
                                if uid:
                                    if allow_any_owner and uid == source_uid and len(owner_candidates) > 1:
                                        fallback_uid = uid
                                        continue
                                    pool.append(uid)
                                    resolved = True
                                    break
                        elif selected.startswith("r") and len(selected) == 2 and selected[1].isdigit():
                            art_idx = int(selected[1]) - 1
                            if 0 <= art_idx < len(p.artifacts):
                                uid = p.artifacts[art_idx]
                                if uid:
                                    if allow_any_owner and uid == source_uid and len(owner_candidates) > 1:
                                        fallback_uid = uid
                                        continue
                                    pool.append(uid)
                                    resolved = True
                                    break
                        elif selected == "b" and p.building:
                            if allow_any_owner and p.building == source_uid and len(owner_candidates) > 1:
                                fallback_uid = p.building
                                continue
                            pool.append(p.building)
                            resolved = True
                            break

                    # If the target was not resolved through the specified syntax and zones, but a fallback UID was identified (e.g., when the selected target matches the source card and the specification allows for any owner), add the fallback UID to the pool.
                    if not resolved and fallback_uid:
                        pool.append(fallback_uid)
                        resolved = True

                    # If the target was still not resolved, attempt to match the selected token against selectable targets based on the current game state and the criteria defined in the `TargetSpec`. This allows for more flexible targeting where the player can specify a token that matches certain characteristics of potential targets, rather than relying solely on specific syntax or UIDs.
                    if not resolved and selected not in engine.state.instances:
                        selectable = self._collect_selectable_targets_for_manual_target(engine, owner_idx, target)
                        for candidate_uid in selectable:
                            if _norm(engine.state.instances[candidate_uid].definition.name) == _norm(selected):
                                pool.append(candidate_uid)
                                break
        elif ttype == "all_saints_on_field":
            pool.extend(engine.all_saints_on_field(0))
            pool.extend(engine.all_saints_on_field(1))
        else:
            return []

        # After collecting potential targets into the pool based on the target type and specifications, filter the pool according to the criteria defined in the `TargetSpec` using the `_filter_target_pool` method. This allows for further refinement of the targets based on additional conditions or attributes specified in the `TargetSpec`. Finally, if a `max_targets` limit is specified in the `TargetSpec`, return only up to that number of targets from the filtered pool.
        out = self._filter_target_pool(engine, owner_idx, target, pool)
        if target.max_targets is not None and target.max_targets >= 0:
            return out[: int(target.max_targets)]
        return out

    # This helper function provides a template for initializing player-specific flags in the runtime state. It returns a dictionary with default values for various flags related to the player's turn ownership, current phase of the game, and other state information that will be used to determine what actions the player can take and the status of their saints on the field. This template is used when ensuring that the runtime state is properly initialized for each player in the game engine's state flags.
    def _resolve_owner_scope(self, owner_idx: int, owner_key: str | None) -> int:
        key = _norm(owner_key or "me")
        return owner_idx if key in {"me", "owner", "controller"} else 1 - owner_idx

    # This helper function determines the relevant player indices based on the owner index and the owner key specified in the target. It normalizes the owner key and checks if it indicates that the targets should be from the opponent, any player, or just the owner. Based on this, it returns a list of player indices that should be considered when resolving targets for effects. This allows for flexible targeting specifications where effects can apply to the owner's cards, the opponent's cards, or both players' cards depending on the context of the effect.
    def _target_owner_indices(self, owner_idx: int, owner_key: str | None) -> list[int]:
        key = _norm(owner_key or "me")
        if key in {"opponent", "enemy", "other"}:
            return [1 - owner_idx]
        if key in {"any", "both", "all", "either"}:
            return [owner_idx, 1 - owner_idx]
        return [owner_idx]

    def _shuffle_graveyard_if_oltretomba_active(self, engine: GameEngine, player_idx: int) -> None:
        promise_state = dict(
            engine.state.flags.get("oltretomba_promise_active", {"0": False, "1": False}) or {"0": False, "1": False}
        )
        if bool(promise_state.get(str(player_idx), False)):
            engine.rng.shuffle(engine.state.players[player_idx].graveyard)

    # This method retrieves the list of card UIDs in a specified zone for a given player. It normalizes the zone name and checks which zone is being requested (e.g., deck, hand, graveyard, field) and returns the corresponding list of card UIDs from the player's state. For the field zone, it combines the attack, defense, artifacts, and building zones to return all cards currently on the field for that player. This method is used to access the cards in different zones when resolving effects that target specific zones or when applying effects that move cards between zones.
    def _get_zone_cards(self, engine: GameEngine, owner_idx: int, zone_name: str) -> list[str]:
        player = engine.state.players[owner_idx]
        zone = _norm(zone_name)
        promise_state = dict(engine.state.flags.get("oltretomba_promise_active", {"0": False, "1": False}) or {"0": False, "1": False})
        promise_active = bool(promise_state.get(str(owner_idx), False))

        # The following block checks the specified zone and returns the corresponding list of card UIDs for that zone. It handles various zones such as deck, hand, graveyard, excommunicated, and field. For the field zone, it combines the attack, defense, artifacts, and building zones to return all cards currently on the field for that player. This allows for easy access to the cards in different zones when resolving effects that target specific zones or when applying effects that move cards between zones.
        if zone in {"deck", "relicario", "graveyard"}:
            if promise_active:
                # When Promessa dell'oltretomba is active, deck and graveyard are the same logical zone.
                # Return cards from both graveyard and deck so queries counting either zone include both pools.
                # Preserve graveyard order first and avoid duplicates.
                merged = list(player.graveyard) + [uid for uid in player.deck if uid not in player.graveyard]
                return merged
            if zone in {"deck", "relicario"}:
                return list(player.deck)
            return list(player.graveyard)
        if zone == "hand":
            return list(player.hand)
        if zone == "excommunicated":
            return list(player.excommunicated)

        # For the field zone, combine the attack, defense, artifacts, and building zones to return all cards currently on the field for that player. This allows for easy access to all cards on the field when resolving effects that target the field or when applying effects that interact with cards on the field.
        out: list[str] = []
        if zone == "field":
            for uid in player.attack + player.defense + player.artifacts:
                if uid:
                    out.append(uid)
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
        return out

    # This method removes a specified card UID from all zones of a given player. It checks each zone (hand, deck, graveyard, excommunicated, attack, defense, artifacts, building) for the presence of the UID and removes it if found. For cards on the field (attack, defense, artifacts), if a card is removed from the attack zone and there is a corresponding card in the defense zone, it promotes the defense card to the attack zone. This method is used to ensure that when a card is moved or removed from play, it is properly taken out of all zones where it might be present for that player.
    def _remove_uid_from_all_player_zones(self, engine: GameEngine, owner_idx: int, uid: str) -> bool:
        player = engine.state.players[owner_idx]

        if uid in player.hand:
            player.hand.remove(uid)
            return True
        if uid in player.deck:
            player.deck.remove(uid)
            return True
        if uid in player.graveyard:
            player.graveyard.remove(uid)
            return True
        if uid in player.excommunicated:
            player.excommunicated.remove(uid)
            return True

        # The following block iterates through the attack, defense, and artifacts zones to find and remove the specified UID. If the UID is found in the attack zone, it checks if there is a corresponding card in the defense zone at the same slot. If there is a card in the defense zone and the attack slot becomes empty after removal, it promotes the defense card to the attack zone and clears the defense slot. This ensures that the game state remains consistent when cards are removed from play, especially when they are on the field.
        for zone_list in (player.attack, player.defense, player.artifacts):
            for i, slot_uid in enumerate(zone_list):
                if slot_uid == uid:
                    zone_list[i] = None
                    if zone_list is player.attack:
                        back_uid = player.defense[i]
                        if back_uid is not None and player.attack[i] is None:
                            player.attack[i] = back_uid
                            player.defense[i] = None
                            engine.state.log(
                                f"{engine.state.instances[back_uid].definition.name} avanza dalla difesa all'attacco."
                            )
                    return True

        if player.building == uid:
            player.building = None
            return True

        return False

    # This method moves a specified card UID to a target zone for a given player. It first checks if the card instance exists and retrieves the real owner of the card. It then determines the current zone of the card and whether it is leaving the field. Depending on the target zone, it performs the necessary operations to move the card, such as adding it to the player's hand, deck, graveyard, or field. If the card is moving from the field, it resets its runtime state. The method returns True if the move was successful and False if it was not possible (e.g., if trying to move a card to hand when the hand is full).
    def _move_uid_to_zone(self, engine: GameEngine, uid: str, to_zone: str, owner_idx: int) -> bool:
        inst = engine.state.instances.get(uid)
        if inst is None:
            return False

        real_owner = inst.owner
        player = engine.state.players[real_owner]
        zone = _norm(to_zone)
        from_zone = engine._locate_uid_zone(real_owner, uid)
        leaving_field = from_zone in {"attack", "defense", "artifact", "building"}

        # The following block handles moving the card to the hand zone. It checks if the card is already in the player's hand, and if not, it checks if there is space in the hand (not exceeding MAX_HAND). If there is space, it removes the card from all other zones and adds it to the player's hand. If the card is leaving the field, it also resets its runtime state. This ensures that the card is properly moved to the hand while respecting game rules such as hand size limits.
        if zone == "hand":
            if uid in player.hand:
                return True
            if len(player.hand) >= MAX_HAND:
                return False
            self._remove_uid_from_all_player_zones(engine, real_owner, uid)
            if leaving_field:
                engine._reset_card_runtime_state(uid)
            player.hand.append(uid)
            return True

        # For other zones (deck, graveyard, excommunicated, field), the method removes the card from all other zones and adds it to the target zone. If the card is leaving the field, it resets its runtime state. The method returns True if the move was successful and False if it was not possible (e.g., if trying to move a card to an unsupported zone).
        self._remove_uid_from_all_player_zones(engine, real_owner, uid)
        if leaving_field:
            engine._reset_card_runtime_state(uid)

        def _shuffle_graveyard_if_promise_active() -> None:
            promise_state = dict(
                engine.state.flags.get("oltretomba_promise_active", {"0": False, "1": False})
                or {"0": False, "1": False}
            )
            if bool(promise_state.get(str(real_owner), False)):
                engine.rng.shuffle(player.graveyard)

        # The following block handles moving the card to the deck. If the card is not already in the deck, it adds it to the bottom of the deck. If the card is already in the deck, it moves it to the bottom. This ensures that the card is properly placed in the deck according to game rules.
        if zone in {"deck_bottom", "bottom_of_deck"}:
            promise_state = dict(engine.state.flags.get("oltretomba_promise_active", {"0": False, "1": False}) or {"0": False, "1": False})
            promise_active = bool(promise_state.get(str(real_owner), False))
            if promise_active:
                if uid not in player.graveyard:
                    player.graveyard.insert(0, uid)
                else:
                    player.graveyard.insert(0, player.graveyard.pop(player.graveyard.index(uid)))
                _shuffle_graveyard_if_promise_active()
                return True
            if uid not in player.deck:
                player.deck.insert(0, uid)
            else:
                player.deck.insert(0, player.deck.pop(player.deck.index(uid)))
            return True

        # For the relicario zone, it treats it the same as the deck, adding the card to the bottom if it's not already there. This allows for effects that move cards to the relicario to function similarly to moving cards to the deck, while still keeping them in a separate zone for game mechanics purposes.
        if zone in {"deck", "relicario"}:
            promise_state = dict(engine.state.flags.get("oltretomba_promise_active", {"0": False, "1": False}) or {"0": False, "1": False})
            promise_active = bool(promise_state.get(str(real_owner), False))
            if promise_active:
                if uid not in player.graveyard:
                    player.graveyard.append(uid)
                _shuffle_graveyard_if_promise_active()
                return True
            if uid not in player.deck:
                player.deck.append(uid)
            return True

        # The following block handles moving the card to the graveyard. If the card is not already in the graveyard, it adds it to the graveyard. This allows for effects that move cards to the graveyard to function properly, ensuring that the card is placed in the correct zone for game mechanics purposes.
        if zone == "graveyard":
            if uid not in player.graveyard:
                player.graveyard.append(uid)
            _shuffle_graveyard_if_promise_active()
            return True

        # The following block handles moving the card to the excommunicated zone. If the card is not already in the excommunicated zone, it adds it to that zone. This allows for effects that move cards to the excommunicated zone to function properly, ensuring that the card is placed in the correct zone for game mechanics purposes.
        if zone == "excommunicated":
            if uid not in player.excommunicated:
                player.excommunicated.append(uid)
            return True

        return False

    # This method retrieves the UID of the card that is currently equipped to a given equipment UID. It checks the blessed tags of the equipment instance for a tag that indicates which card it is equipped to (in the format "equipped_to:target_uid"). If such a tag is found, it returns the target UID. If no such tag is found or if the equipment instance does not exist, it returns None. This method is used to determine which card is currently benefiting from an equipment's effects.
    def _equipment_target_uid(self, engine: GameEngine, equipment_uid: str) -> str | None:
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

    # This method clears the equipment link for a given equipment UID. It retrieves the equipment instance and checks its blessed tags for any tag that indicates which card it is equipped to. If such a tag is found, it removes that tag from the equipment's blessed list and also removes the corresponding "equipped_by:equipment_uid" tag from the target card's blessed list. This effectively breaks the link between the equipment and the card it was equipped to. The method returns the target UID that was previously equipped, or None if there was no valid equipment instance or no equipped target.
    def _clear_equipment_link(self, engine: GameEngine, equipment_uid: str) -> str | None:
        equipment = engine.state.instances.get(equipment_uid)
        if equipment is None:
            return None
        target_uid = self._equipment_target_uid(engine, equipment_uid)
        equipment.blessed = [
            tag for tag in equipment.blessed if not (isinstance(tag, str) and tag.startswith("equipped_to:"))
        ]
        if target_uid and target_uid in engine.state.instances:
            target_inst = engine.state.instances[target_uid]
            target_inst.blessed = [
                tag for tag in target_inst.blessed if str(tag) != f"equipped_by:{equipment_uid}"
            ]
        return target_uid

    # This method places a specified equipment UID onto the field for a given player. It first checks if the equipment is already in the player's artifacts zone, and if so, it returns True. If not, it looks for an empty slot in the artifacts zone. If there are no empty slots, it takes the last slot and sends any existing equipment in that slot to the graveyard. It then removes the equipment UID from all other zones of the player and places it in the determined slot in the artifacts zone. The method returns True if the equipment was successfully placed on the field.
    def _place_equipment_on_field(self, engine: GameEngine, owner_idx: int, uid: str) -> bool:
        player = engine.state.players[owner_idx]
        if uid in player.artifacts:
            return True

        slot = next((i for i, slot_uid in enumerate(player.artifacts) if slot_uid is None), None)
        if slot is None:
            slot = len(player.artifacts) - 1
            replaced_uid = player.artifacts[slot]
            if replaced_uid:
                engine.send_to_graveyard(engine.state.instances[replaced_uid].owner, replaced_uid)
        self._remove_uid_from_all_player_zones(engine, owner_idx, uid)
        player.artifacts[slot] = uid
        return True

    # This method summons a token onto the field for a given player. It takes the token name and an optional preferred zone (attack or defense) as parameters. It looks up the token definition in the cards.json file, creates a new card instance for the token, and places it in the appropriate zone based on the preferred zone and available space. If the preferred zone is full, it tries to place the token in the other zone. If there is no space in either zone, it logs a message and returns None. If the token is successfully summoned, it emits relevant events and resolves any "enter field" effects associated with the token.
    def _summon_generated_token(
        self,
        engine: GameEngine,
        owner_idx: int,
        token_name: str,
        preferred_zone: str | None = None,
    ) -> str | None:
        token_key = _norm(token_name)
        # runtime_sections/* lives under holywar/effects/runtime_sections;
        # cards.json is in holywar/data.
        cards_path = Path(__file__).resolve().parents[2] / "data" / "cards.json"
        card_defs = load_cards_json(cards_path)

        token_def = next((c for c in card_defs if _norm(c.name) == token_key), None)
        if token_def is None:
            engine.state.log(f"Token non trovato in cards.json: {token_name}.")
            return None

        player = engine.state.players[owner_idx]

        preferred = _norm(preferred_zone or "")
        slot = None
        zone = ""

        # The following block determines where to place the summoned token based on the preferred zone and available space. If the preferred zone is defense, it first tries to find an open slot in the defense zone, and if none are available, it tries the attack zone. If the preferred zone is attack, it first tries the attack zone, and if none are available, it tries the defense zone. If no preferred zone is specified, it defaults to trying the attack zone first and then the defense zone. If there is no space in either zone, it logs a message indicating that there is no space to summon the token and returns None.
        if preferred == "defense":
            slot = engine._first_open(player.defense)
            zone = "defense"
            if slot is None:
                slot = engine._first_open(player.attack)
                zone = "attack"
        elif preferred == "attack":
            slot = engine._first_open(player.attack)
            zone = "attack"
            if slot is None:
                slot = engine._first_open(player.defense)
                zone = "defense"
        else:
            slot = engine._first_open(player.attack)
            zone = "attack"
            if slot is None:
                slot = engine._first_open(player.defense)
                zone = "defense"
        if slot is None:
            engine.state.log(f"{player.name} non ha spazio per evocare {token_name}.")
            return None

        # To generate a unique UID for the new token instance, the method looks through all existing instances in the game state to find the maximum numeric suffix used in UIDs that start with "c". It then creates a new UID by incrementing this maximum number and formatting it as "cXXXXX" where XXXXX is a zero-padded number. This ensures that the new token instance has a unique identifier that does not conflict with existing instances.
        max_num = 0
        for uid in engine.state.instances:
            if uid.startswith("c"):
                try:
                    max_num = max(max_num, int(uid[1:]))
                except ValueError:
                    pass
        new_uid = f"c{max_num + 1:05d}"

        # The method creates a new card instance for the token using the token definition. It copies the token definition to ensure that the new instance has its own separate definition data. It then adds the new instance to the game state with the generated UID, setting its owner, current faith, and other relevant attributes. Finally, it places the new token in the appropriate zone on the field and emits events related to the token entering the field and being summoned.
        token_copy = CardDefinition.from_dict(token_def.to_dict())
        engine.state.instances[new_uid] = CardInstance(
            uid=new_uid,
            definition=token_copy,
            owner=owner_idx,
            current_faith=token_copy.faith,
        )

        # Depending on the determined zone (attack or defense), the method places the new token in the appropriate slot for that zone. It then emits events to indicate that the token has entered the field and has been summoned, allowing other effects and game mechanics to respond to these events as needed.
        if zone == "attack":
            player.attack[slot] = new_uid
        else:
            player.defense[slot] = new_uid

        inst = engine.state.instances[new_uid]
        inst.exhausted = False

        engine.state.log(f"{player.name} evoca il token {inst.definition.name} in {zone} {slot + 1}.")
        engine._emit_event("on_enter_field", owner_idx, card=new_uid, from_zone="generated")
        engine._emit_event("on_token_summoned", owner_idx, token=new_uid, summoner=owner_idx)

        enter_msg = self.resolve_enter(engine, owner_idx, new_uid)
        if enter_msg:
            engine.state.log(str(enter_msg))

        return new_uid

    # This method applies a specified effect to a list of target UIDs. It first normalizes the action specified in the effect and checks if it matches any known effect actions or aliases. Depending on the action, it performs the corresponding operations to apply the effect to the target instances. For example, it can increase faith, increase strength, grant attack barriers, prevent attacks, negate activations, grant extra attacks, equip or unequip cards, and destroy equipment. The method also checks if the effect usage can be applied based on the game state and ensures that any necessary conditions are met before applying the effect.
    def _apply_effect(
        self,
        engine: GameEngine,
        owner_idx: int,
        source_uid: str,
        targets: list[str],
        effect: EffectSpec,
    ) -> None:
        action = _norm(effect.action)
        action = EFFECT_ACTION_ALIASES.get(action, action)
        if action == "return_to_hand_once_per_turn":
            self._apply_return_to_hand_once_per_turn(engine, owner_idx, source_uid, targets)
            return
        if not self._effect_usage_can_use(engine, owner_idx, source_uid, effect):
            return
        if action == "increase_faith":
            for t_uid in targets:
                inst = engine.state.instances[t_uid]
                inst.current_faith = (inst.current_faith or 0) + int(effect.amount)
                if _norm(effect.duration) in {"until_source_leaves", "while_source_on_field", "source_bound"}:
                    marker = f"runtime_faith:{source_uid}:{int(effect.amount)}"
                    inst.blessed.append(marker)
                    ek = id(engine)
                    by_source = self._temp_faith.setdefault(ek, {}).setdefault(source_uid, [])
                    by_source.append((t_uid, int(effect.amount), marker))
            return
        if action == "increase_strength":
            for t_uid in targets:
                engine.state.instances[t_uid].blessed.append(f"buff_str:{int(effect.amount)}")
            return
        if action == "grant_attack_barrier":
            charges = max(1, int(effect.amount or 1))
            for t_uid in targets:
                inst = engine.state.instances.get(t_uid)
                if inst is None:
                    continue
                for _ in range(charges):
                    inst.blessed.append(f"barrier_once:attack:{source_uid}")
            return
        if action == "grant_blessed_tag_from_source":
            tag_base = str(effect.flag or "").strip()
            if not tag_base:
                return
            for t_uid in targets:
                inst = engine.state.instances.get(t_uid)
                if inst is None:
                    continue
                marker = f"{tag_base}:{source_uid}"
                if marker not in inst.blessed:
                    inst.blessed.append(marker)
            return
        if action == "prevent_specific_card_from_attacking":
            duration_turns = max(1, int(effect.amount or 1))
            until_turn = int(engine.state.turn_number) + duration_turns - 1
            tag = f"no_attack_until:{until_turn}"
            for t_uid in targets:
                inst = engine.state.instances.get(t_uid)
                if inst is None:
                    continue
                if tag not in inst.cursed:
                    inst.cursed.append(tag)
            return
        if action == "negate_next_activation":
            duration_turns = max(1, int(effect.amount or 1))
            until_turn = int(engine.state.turn_number) + duration_turns - 1
            tag = f"no_activate_until:{until_turn}"
            for t_uid in targets:
                inst = engine.state.instances.get(t_uid)
                if inst is None:
                    continue
                if tag not in inst.cursed:
                    inst.cursed.append(tag)
            return
        if action == "grant_counter_spell":
            target = self._resolve_player_scope(owner_idx, effect.target_player or "me")
            amount = max(1, int(effect.amount or 1))
            flags = engine.state.flags.setdefault("counter_spell_ready", {"0": 0, "1": 0})
            key = str(target)
            flags[key] = int(flags.get(key, 0)) + amount
            return
        if action == "grant_extra_attack_this_turn":
            current_turn = int(engine.state.turn_number)
            tag = f"extra_attack_turn:{current_turn}"
            for t_uid in targets:
                inst = engine.state.instances.get(t_uid)
                if inst is None:
                    continue
                inst.blessed = [t for t in inst.blessed if not (isinstance(t, str) and t.startswith("extra_attack_turn:"))]
                inst.blessed.append(tag)
            return
        if action == "equip_card":
            source_inst = engine.state.instances.get(source_uid)
            if source_inst is None:
                return
            for t_uid in targets:
                target_inst = engine.state.instances.get(t_uid)
                if target_inst is None:
                    continue
                if not self._is_uid_on_field(engine, t_uid):
                    continue
                previous_target = self._clear_equipment_link(engine, source_uid)
                if not self._place_equipment_on_field(engine, source_inst.owner, source_uid):
                    if previous_target and previous_target in engine.state.instances:
                        source_inst.blessed.append(f"equipped_to:{previous_target}")
                        prev_inst = engine.state.instances[previous_target]
                        if f"equipped_by:{source_uid}" not in prev_inst.blessed:
                            prev_inst.blessed.append(f"equipped_by:{source_uid}")
                    continue
                source_inst.blessed.append(f"equipped_to:{t_uid}")
                equip_tag = f"equipped_by:{source_uid}"
                if equip_tag not in target_inst.blessed:
                    target_inst.blessed.append(equip_tag)
                engine._emit_event(
                    "on_player_equips_card",
                    owner_idx,
                    card=source_uid,
                    equipment=source_uid,
                    target=t_uid,
                )
                break
            return
        if action == "unequip_card":
            to_zone = str(effect.to_zone or "").strip()
            for t_uid in targets:
                inst = engine.state.instances.get(t_uid)
                if inst is None:
                    continue
                target_uid = self._clear_equipment_link(engine, t_uid)
                engine._emit_event(
                    "on_player_unequips_card",
                    owner_idx,
                    card=t_uid,
                    equipment=t_uid,
                    target=target_uid,
                )
                if to_zone:
                    self._move_uid_to_zone(engine, t_uid, to_zone, inst.owner)
            return
        if action == "destroy_equipment":
            for t_uid in targets:
                inst = engine.state.instances.get(t_uid)
                if inst is None:
                    continue
                target_uid = self._clear_equipment_link(engine, t_uid)
                engine._emit_event(
                    "on_player_unequips_card",
                    owner_idx,
                    card=t_uid,
                    equipment=t_uid,
                    target=target_uid,
                )
                engine.send_to_graveyard(inst.owner, t_uid)
            return
        if action == "absorb_target_stats_and_link":
            source_inst = engine.state.instances.get(source_uid)
            if source_inst is None:
                return
            for t_uid in targets:
                target_inst = engine.state.instances.get(t_uid)
                if target_inst is None:
                    continue
                gain_faith = max(0, int(target_inst.current_faith or 0))
                gain_strength = max(0, int(engine.get_effective_strength(t_uid)))
                source_inst.current_faith = max(0, int(source_inst.current_faith or 0) + gain_faith)
                if gain_strength > 0:
                    source_inst.blessed.append(f"buff_str:{gain_strength}")
                link_tag = f"levigata_link:{t_uid}"
                if link_tag not in source_inst.blessed:
                    source_inst.blessed.append(link_tag)
                break
            return
        if action == "decrease_strength":
            amount = max(0, int(effect.amount))
            if amount <= 0:
                return
            for t_uid in targets:
                engine.state.instances[t_uid].blessed.append(f"buff_str:{-amount}")
            return
        if action == "halve_strength_rounded_down":
            for t_uid in targets:
                inst = engine.state.instances.get(t_uid)
                if inst is None:
                    continue
                current_strength = max(0, int(engine.get_effective_strength(t_uid)))
                reduced = current_strength // 2
                delta = current_strength - reduced
                if delta > 0:
                    inst.blessed.append(f"buff_str:{-delta}")
            return
        if action == "halve_target_base_faith_rounded_down":
            for t_uid in targets:
                inst = engine.state.instances.get(t_uid)
                if inst is None:
                    continue
                base_faith = int(inst.definition.faith or 0)
                halved = max(0, base_faith // 2)
                inst.definition.faith = halved
                if inst.current_faith is not None and int(inst.current_faith) > halved:
                    inst.current_faith = halved
            return
        if action == "retaliate_damage_to_event_source_if_enemy_saint":
            dmg = max(0, int(effect.amount or 0))
            if dmg <= 0:
                return
            source_inst = engine.state.instances.get(source_uid)
            if source_inst is None:
                return
            attacker_uid = str(engine.state.flags.get("_runtime_event_source", "")).strip()
            if not attacker_uid or attacker_uid not in engine.state.instances:
                return
            attacker_inst = engine.state.instances[attacker_uid]
            if int(attacker_inst.owner) == int(owner_idx):
                return
            if _norm(attacker_inst.definition.card_type) not in {"santo", "token"}:
                return
            dmg = engine._apply_damage_mitigation(attacker_inst.owner, dmg, target_uid=attacker_uid)
            if dmg <= 0:
                return
            before = attacker_inst.current_faith or 0
            attacker_inst.current_faith = max(0, (attacker_inst.current_faith or 0) - dmg)
            after = attacker_inst.current_faith or 0
            engine.state.log(
                f"{attacker_inst.definition.name} subisce {dmg} danni di ritorsione (Fede {before}->{after})."
            )
            if (attacker_inst.current_faith or 0) <= 0:
                engine.destroy_saint_by_uid(attacker_inst.owner, attacker_uid, cause="effect")
            return
        if action == "destroy_source_if_linked_to_event_card":
            source_inst = engine.state.instances.get(source_uid)
            if source_inst is None:
                return
            event_uid = str(engine.state.flags.get("_runtime_event_card", "")).strip()
            if not event_uid:
                return
            link_tag = f"levigata_link:{event_uid}"
            if link_tag not in source_inst.blessed:
                return
            engine.destroy_saint_by_uid(source_inst.owner, source_uid, cause="effect")
            return
        if action == "destroy_source_if_equipped_target_is_event_card":
            source_inst = engine.state.instances.get(source_uid)
            if source_inst is None:
                return
            event_uid = str(engine.state.flags.get("_runtime_event_card", "")).strip()
            if not event_uid:
                return
            equipped_uid = self._equipment_target_uid(engine, source_uid)
            if not equipped_uid or equipped_uid != event_uid:
                return
            engine.destroy_any_card(source_inst.owner, source_uid)
            return
        if action == "move_source_to_zone_if_equipped_target_is_event_card":
            source_inst = engine.state.instances.get(source_uid)
            if source_inst is None:
                return
            event_uid = str(engine.state.flags.get("_runtime_event_card", "")).strip()
            if not event_uid:
                return
            equipped_uid = self._equipment_target_uid(engine, source_uid)
            if not equipped_uid or equipped_uid != event_uid:
                return
            to_zone = str(effect.to_zone or "").strip()
            if not to_zone:
                return
            self._move_uid_to_zone(engine, source_uid, to_zone, source_inst.owner)
            return
        if action == "inflict_sin_to_event_owner_equal_base_faith_if_equipped_target":
            event_uid = str(engine.state.flags.get("_runtime_event_card", "")).strip()
            if not event_uid or event_uid not in engine.state.instances:
                return
            equipped_uid = self._equipment_target_uid(engine, source_uid)
            if not equipped_uid or equipped_uid != event_uid:
                return
            event_inst = engine.state.instances[event_uid]
            amount = max(0, int(event_inst.definition.faith or 0))
            if amount <= 0:
                return
            engine.gain_sin(int(event_inst.owner), amount)
            return
        if action == "reveal_stored_card":
            store_name = str(effect.stored or "").strip()
            if not store_name:
                return

            stored_uid = str(engine.state.flags.get(f"_runtime_store_{store_name}", "")).strip()
            if not stored_uid:
                return

            engine.state.flags["_runtime_reveal_card"] = stored_uid
            engine.state.flags["_runtime_waiting_for_reveal"] = True
            return
        if action == "reveal_selected_target":
            selected_uid = self._selected_target_uid_for_current_action(engine, owner_idx)
            if not selected_uid:
                return
            engine.state.flags["_runtime_reveal_card"] = selected_uid
            engine.state.flags["_runtime_waiting_for_reveal"] = True
            return
        if action == "add_temporary_inspiration":
            target = self._resolve_player_scope(owner_idx, effect.target_player or "me")
            player = engine.state.players[target]
            player.temporary_inspiration = max(
                0,
                int(getattr(player, "temporary_inspiration", 0)) + int(effect.amount)
            )
            return
        
        if action == "store_target_strength":
            flag_name = str(effect.flag or "").strip()
            if not flag_name:
                return

            value = 0
            for t_uid in targets:
                inst = engine.state.instances.get(t_uid)
                if inst is None:
                    continue

                base = int(inst.definition.strength or 0)
                bonus = 0

                for tag in list(inst.blessed) + list(inst.cursed):
                    if isinstance(tag, str) and tag.startswith("buff_str:"):
                        try:
                            bonus += int(tag.split(":", 1)[1])
                        except ValueError:
                            pass

                value = max(0, base + bonus)
                break

            engine.state.flags[flag_name] = value
            return

        if action == "store_target_faith":
            flag_name = str(effect.flag or "").strip()
            if not flag_name:
                return

            value = 0
            for t_uid in targets:
                inst = engine.state.instances.get(t_uid)
                if inst is None:
                    continue
                value = max(0, int(inst.current_faith or 0))
                break

            engine.state.flags[flag_name] = value
            return
        if action == "store_target_faith_and_excommunicate_no_sin":
            flag_name = str(effect.flag or "").strip()
            if not flag_name:
                return

            value = 0
            selected_uid: str | None = None
            for t_uid in targets:
                inst = engine.state.instances.get(t_uid)
                if inst is None:
                    continue
                value = max(0, int(inst.current_faith or 0))
                selected_uid = t_uid
                break

            engine.state.flags[flag_name] = value
            if selected_uid:
                target_inst = engine.state.instances.get(selected_uid)
                if target_inst is not None:
                    engine.excommunicate_card(target_inst.owner, selected_uid)
            return
        
        if action == "store_top_card_of_zone":
            store_name = str(effect.store_as or "").strip()
            if not store_name:
                return

            scoped_owner = self._resolve_owner_scope(owner_idx, effect.owner or "me")
            zone_name = str(effect.zone or "deck").strip()
            position = _norm(effect.position or "top")

            cards = self._get_zone_cards(engine, scoped_owner, zone_name)

            picked_uid = ""
            if cards:
                picked_uid = cards[-1] if position == "top" else cards[0]

            engine.state.flags[f"_runtime_store_{store_name}"] = picked_uid
            return
        
        if action == "move_stored_card_to_zone":
            store_name = str(effect.stored or "").strip()
            to_zone = str(effect.to_zone or "").strip()
            if not store_name or not to_zone:
                return

            stored_uid = str(engine.state.flags.get(f"_runtime_store_{store_name}", "")).strip()
            if not stored_uid:
                return

            self._move_uid_to_zone(engine, stored_uid, to_zone, owner_idx)
            return
        
        if action == "summon_stored_card_to_field":
            store_name = str(effect.stored or "").strip()
            if not store_name:
                return

            stored_uid = str(engine.state.flags.get(f"_runtime_store_{store_name}", "")).strip()
            if not stored_uid or stored_uid not in engine.state.instances:
                return

            self._apply_effect(
                engine,
                owner_idx,
                source_uid,
                EffectSpec(action="summon_target_to_field"),
                [stored_uid],
            )
            return
        
        if action == "move_source_to_zone":
            to_zone = str(effect.to_zone or "").strip()
            if not source_uid or not to_zone:
                return

            self._move_uid_to_zone(engine, source_uid, to_zone, owner_idx)
            return
         
        if action == "add_temporary_inspiration_from_flag":
            flag_name = str(effect.flag or "").strip()
            if not flag_name:
                return

            raw_value = engine.state.flags.get(flag_name, 0)
            try:
                amount = int(raw_value)
            except (TypeError, ValueError):
                amount = 0

            target = self._resolve_player_scope(owner_idx, effect.target_player or "me")
            player = engine.state.players[target]
            player.temporary_inspiration = max(
                0,
                int(getattr(player, "temporary_inspiration", 0)) + amount
            )

            engine.state.flags.pop(flag_name, None)
            return
        
        if action == "gain_inspiration_from_flag":
            flag_name = str(effect.flag or "").strip()
            if not flag_name:
                return

            raw_value = engine.state.flags.get(flag_name, 0)
            try:
                amount = int(raw_value)
            except (TypeError, ValueError):
                amount = 0

            if amount <= 0:
                engine.state.flags.pop(flag_name, None)
                return

            # Adatta questo campo al nome reale che usi per l'ispirazione extra nel turno
            current = int(engine.state.flags.get("_extra_inspiration_this_turn", 0))
            engine.state.flags["_extra_inspiration_this_turn"] = current + amount

            engine.state.flags.pop(flag_name, None)
            return
        
        if action == "store_target_strength":
            flag_name = str(effect.flag or "").strip()
            if not flag_name:
                return

            value = 0
            for t_uid in targets:
                inst = engine.state.instances.get(t_uid)
                if inst is None:
                    continue

                base = inst.definition.strength or 0
                bonus = 0

                for tag in list(inst.blessed) + list(inst.cursed):
                    if isinstance(tag, str) and tag.startswith("buff_str:"):
                        try:
                            bonus += int(tag.split(":", 1)[1])
                        except ValueError:
                            pass

                value = base + bonus
                break

            engine.state.flags[flag_name] = value
            return
        
        if action == "remove_sin_equal_to_target_strength":
            target_player = self._resolve_player_scope(owner_idx, effect.target_player or "me")
            player = engine.state.players[target_player]

            amount = 0
            for t_uid in targets:
                inst = engine.state.instances.get(t_uid)
                if inst is None:
                    continue

                base = int(inst.definition.strength or 0)
                bonus = 0

                for tag in list(inst.blessed) + list(inst.cursed):
                    if isinstance(tag, str) and tag.startswith("buff_str:"):
                        try:
                            bonus += int(tag.split(":", 1)[1])
                        except ValueError:
                            pass

                amount = max(0, base + bonus)
                break

            player.sin = max(0, int(player.sin) - amount)
            return

        if action == "reset_faith_to_base":
            for t_uid in targets:
                inst = engine.state.instances.get(t_uid)
                if inst is None:
                    continue
                if inst.current_faith is None:
                    continue

                base_faith = inst.definition.faith
                if base_faith is None:
                    continue

                inst.current_faith = base_faith

                engine._emit_event(
                    "on_faith_modified",
                    inst.owner,
                    card=t_uid,
                    amount=0,
                )
            return
        if action == "set_faith_to":
            value = max(0, int(effect.amount))
            for t_uid in targets:
                inst = engine.state.instances.get(t_uid)
                if inst is None:
                    continue
                inst.current_faith = value
                if value <= 0 and _norm(inst.definition.card_type) in {"santo", "token"}:
                    engine.destroy_saint_by_uid(inst.owner, t_uid, cause="effect")
            return
        
        if action == "summon_target_to_field":
            for t_uid in targets:
                inst = engine.state.instances.get(t_uid)
                if inst is None:
                    continue

                owner = inst.owner
                board_owner = owner
                player = engine.state.players[owner]
                ctype = _norm(inst.definition.card_type)
                if ctype == _norm("santo") and self._has_invert_saint_summon_aura(engine):
                    board_owner = 1 - board_owner
                board_player = engine.state.players[board_owner]

                if t_uid in player.hand:
                    player.hand.remove(t_uid)
                elif t_uid in player.deck:
                    player.deck.remove(t_uid)
                elif t_uid in player.graveyard:
                    player.graveyard.remove(t_uid)
                elif t_uid in player.excommunicated:
                    player.excommunicated.remove(t_uid)
                elif t_uid in player.attack:
                    player.attack[player.attack.index(t_uid)] = None
                elif t_uid in player.defense:
                    player.defense[player.defense.index(t_uid)] = None
                elif t_uid in player.artifacts:
                    player.artifacts[player.artifacts.index(t_uid)] = None
                elif player.building == t_uid:
                    player.building = None

                placed = False

                if ctype == _norm("artefatto"):
                    blocked = 0
                    opponent = engine.state.players[1 - owner]
                    enemy_field_uids = [cand for cand in (opponent.attack + opponent.defense + opponent.artifacts) if cand]
                    if opponent.building:
                        enemy_field_uids.append(opponent.building)
                    for enemy_uid in enemy_field_uids:
                        enemy_name = engine.state.instances[enemy_uid].definition.name
                        blocked += int(self.get_blocks_enemy_artifact_slots(enemy_name))
                    blocked = min(state.ARTIFACT_SLOTS - 1, blocked)
                    usable_slots = list(range(state.ARTIFACT_SLOTS - blocked))
                    if usable_slots:
                        slot = next((i for i in usable_slots if player.artifacts[i] is None), None)
                        if slot is None:
                            slot = usable_slots[-1]
                            replaced = player.artifacts[slot]
                            if replaced:
                                engine.send_to_graveyard(owner, replaced)
                        player.artifacts[slot] = t_uid
                        placed = True

                elif ctype == _norm("edificio"):
                    if player.building is None:
                        player.building = t_uid
                        placed = True

                else:
                    slot = engine._first_open(board_player.attack)
                    zone = "attack"
                    if slot is None:
                        slot = engine._first_open(board_player.defense)
                        zone = "defense"
                    if slot is not None and engine.place_card_from_uid(board_owner, t_uid, zone, slot):
                        placed = True

                if not placed:
                    self._move_uid_to_zone(engine, t_uid, "deck_bottom", owner)
                    continue

                inst.exhausted = False
                engine._emit_event("on_enter_field", owner, card=t_uid, from_zone="deck")
            return

        if action == "return_to_hand":
            for uid in targets:
                inst = engine.state.instances.get(uid)
                if inst is None:
                    continue

                owner = inst.owner
                if not engine.move_board_card_to_hand(owner, uid):
                    continue
                self._effect_usage_consume(engine, owner_idx, source_uid, effect)
                engine._emit_event("on_this_card_leaves_field", owner, card=uid, destination="hand")
            return
        if action == "send_to_graveyard":
            for t_uid in targets:
                inst = engine.state.instances.get(t_uid)
                if inst is None:
                    continue

                owner = inst.owner
                player = engine.state.players[owner]

                # Caso: carta in mano → SCARTO
                if t_uid in player.hand:
                    player.hand.remove(t_uid)
                    if t_uid not in player.graveyard:
                        player.graveyard.append(t_uid)
                        self._shuffle_graveyard_if_oltretomba_active(engine, owner)

                    engine._emit_event(
                        "on_card_discarded",
                        owner,
                        card=t_uid,
                        from_hand_to_graveyard=True,
                    )

                    engine._emit_event(
                        "on_card_sent_to_graveyard",
                        owner,
                        card=t_uid,
                        from_zone="hand",
                        owner=owner,
                    )
                    self._maybe_auto_activate_discarded_from_hand_by_effect(engine, owner, t_uid, source_uid)
                    continue

                # Caso: carta nel deck
                if t_uid in player.deck:
                    player.deck.remove(t_uid)
                    if t_uid not in player.graveyard:
                        player.graveyard.append(t_uid)
                        self._shuffle_graveyard_if_oltretomba_active(engine, owner)

                    engine._emit_event(
                        "on_card_sent_to_graveyard",
                        owner,
                        card=t_uid,
                        from_zone="relicario",
                        owner=owner,
                    )
                    continue

                # Caso: già nel cimitero
                if t_uid in player.graveyard:
                    continue

                # Caso: carta sul campo → usa funzione già esistente
                engine.send_to_graveyard(owner, t_uid)

            return
        if action == "double_strength":
            for t_uid in targets:
                inst = engine.state.instances[t_uid]
                current = engine.get_effective_strength(t_uid)
                base = max(0, inst.definition.strength or 0)
                bonus = current - base
                inst.definition.strength = max(0, base + bonus)
                inst.blessed.append(f"buff_str:{current}")
            return
        if action == "add_seal_counter":
            amount = max(0, int(effect.amount))
            if amount <= 0:
                return
            engine._set_altare_sigilli(owner_idx, engine._get_altare_sigilli(owner_idx) + amount)
            return
        if action == "remove_seal_counter":
            amount = max(0, int(effect.amount))
            if amount <= 0:
                return
            engine._set_altare_sigilli(owner_idx, max(0, engine._get_altare_sigilli(owner_idx) - amount))
            return
        if action == "decrease_faith":
            amount = int(effect.amount)
            if effect.amount_multiplier_card_name:
                amount *= self._count_named_cards_on_field(engine, effect.amount_multiplier_card_name)
            if amount <= 0:
                return
            for t_uid in targets:
                inst = engine.state.instances[t_uid]
                dmg = amount
                if _norm(inst.definition.card_type) in {"santo", "token"}:
                    dmg = engine._apply_damage_mitigation(inst.owner, dmg, target_uid=t_uid)
                if dmg <= 0:
                    continue
                inst.current_faith = max(0, (inst.current_faith or 0) - dmg)
                if (inst.current_faith or 0) <= 0 and _norm(inst.definition.card_type) in {"santo", "token"}:
                    engine.destroy_saint_by_uid(inst.owner, t_uid, cause="effect")
            return
        if action == "calice_upkeep":
            player = engine.state.players[owner_idx]
            if player.sin >= 5:
                player.sin -= 5
                engine.state.log(f"{player.name} paga 5 Peccato per mantenere Calice Insanguinato.")
            else:
                engine.send_to_graveyard(owner_idx, source_uid)
                engine.state.log(f"{player.name} non puo pagare Calice Insanguinato: la carta viene distrutta.")
            return
        if action == "calice_endturn":
            destroyed = 0
            for s_uid in list(engine.all_saints_on_field(owner_idx)):
                if self.is_immune_to_action(
                    engine.state.instances[s_uid].definition.name,
                    "calice_endturn_destroy",
                ):
                    continue
                engine.destroy_saint_by_uid(owner_idx, s_uid, cause="effect")
                destroyed += 1
            if destroyed > 0:
                engine.gain_sin(1 - owner_idx, destroyed * 5)
            return
        if action == "campana_add_counter":
            inst = engine.state.instances[source_uid]
            counter = 0
            for tag in list(inst.blessed):
                if tag.startswith("campana_counter:"):
                    try:
                        counter = int(tag.split(":", 1)[1])
                    except ValueError:
                        counter = 0
                    inst.blessed.remove(tag)
            counter += 1
            inst.blessed.append(f"campana_counter:{counter}")
            return
        if action == "campana_remove_counter":
            inst = engine.state.instances.get(source_uid)
            if inst is None:
                return
            amount = max(0, int(effect.amount or 0))
            if amount <= 0:
                return
            counter = 0
            for tag in list(inst.blessed):
                if not isinstance(tag, str) or not tag.startswith("campana_counter:"):
                    continue
                try:
                    counter = int(tag.split(":", 1)[1])
                except ValueError:
                    counter = 0
                inst.blessed.remove(tag)
                break
            counter = max(0, counter - amount)
            inst.blessed.append(f"campana_counter:{counter}")
            return
        if action == "cataclisma_ciclico":
            own_saints = engine.all_saints_on_field(owner_idx)
            opp_idx = 1 - owner_idx
            opp_saints = engine.all_saints_on_field(opp_idx)
            if not own_saints and not opp_saints:
                return
            if opp_saints:
                target_uid = opp_saints[0]
                target_owner = opp_idx
            else:
                target_uid = own_saints[0]
                target_owner = owner_idx
            target_name = engine.state.instances[target_uid].definition.name
            engine.destroy_saint_by_uid(target_owner, target_uid, cause="effect")
            if target_owner == owner_idx:
                engine.gain_sin(opp_idx, 2)
                engine.state.log(
                    f"Cataclisma Ciclico distrugge {target_name}: +2 Peccato a {engine.state.players[opp_idx].name}."
                )
            else:
                engine.reduce_sin(owner_idx, 1)
                engine.state.log(
                    f"Cataclisma Ciclico distrugge {target_name}: {engine.state.players[owner_idx].name} perde 1 Peccato."
                )
            return
        if action == "kah_ok_tick":
            inst = engine.state.instances[source_uid]
            inst.current_faith = (inst.current_faith or 0) + 2
            if (inst.current_faith or 0) >= 10:
                gained = max(0, inst.current_faith or 0)
                engine.destroy_saint_by_uid(owner_idx, source_uid, cause="effect")
                engine.gain_sin(owner_idx, gained)
                engine.state.log(
                    f"Kah-ok raggiunge 10 Fede e si distrugge: {engine.state.players[owner_idx].name} +{gained} Peccato."
                )
            return
        if action == "trombe_del_giudizio_tick":
            b_uid = engine.state.players[owner_idx].building
            if b_uid is None:
                return
            if not self.get_is_altare_sigilli(engine.state.instances[b_uid].definition.name):
                return
            seals = engine._get_altare_sigilli(owner_idx)
            if seals >= 7:
                amount = 10
            elif seals >= 5:
                amount = 6
            elif seals >= 3:
                amount = 3
            else:
                amount = 0
            if amount > 0:
                engine.gain_sin(1 - owner_idx, amount)
            return
        if action == "av_drna_on_opponent_draw":
            inst = engine.state.instances[source_uid]
            inst.current_faith = max(0, (inst.current_faith or 0) - 1)
            engine.reduce_sin(owner_idx, 2)
            if (inst.current_faith or 0) <= 0:
                engine.send_to_graveyard(owner_idx, source_uid)
            return
        if action == "phdrna_activate_destroy_target_then_self":
            selected = str(engine.state.flags.get("_runtime_selected_target", "")).strip()
            target_uid = selected if selected in engine.state.instances else None
            if not target_uid:
                return

            selected_option = _norm(str(engine.state.flags.get("_runtime_selected_option", "")))
            player = engine.state.players[owner_idx]
            cost_inspiration = 10

            if selected_option == "building":
                if player.building is None:
                    return
                engine.send_to_graveyard(owner_idx, player.building)
            elif selected_option == "artifacts":
                artifacts = [uid for uid in player.artifacts if uid]
                if len(artifacts) < 4:
                    return
                for art_uid in artifacts[:4]:
                    engine.send_to_graveyard(owner_idx, art_uid)
            else:
                return

            total_inspiration = int(player.inspiration) + int(getattr(player, "temporary_inspiration", 0))
            if total_inspiration < cost_inspiration:
                return

            temp = max(0, int(getattr(player, "temporary_inspiration", 0)))
            use_temp = min(temp, cost_inspiration)
            player.temporary_inspiration = temp - use_temp
            player.inspiration = max(0, int(player.inspiration) - (cost_inspiration - use_temp))

            target_inst = engine.state.instances.get(target_uid)
            if target_inst is not None:
                engine.destroy_any_card(target_inst.owner, target_uid)

            engine.state.flags["_allow_indestructible_uid"] = source_uid
            source_inst = engine.state.instances.get(source_uid)
            if source_inst is not None:
                engine.destroy_any_card(source_inst.owner, source_uid)
            engine.state.flags.pop("_allow_indestructible_uid", None)
            return
        if action == "pay_sin_or_destroy_self":
            cost = max(0, int(effect.amount))
            player = engine.state.players[owner_idx]
            source_inst = engine.state.instances.get(source_uid)
            source_name = source_inst.definition.name if source_inst is not None else source_uid

            if player.sin + cost < 100:
                engine.gain_sin(owner_idx, cost)
                engine.state.log(f"{source_name}: {player.name} accumula {cost} Peccato.")
            else:
                engine.state.log(
                    f"{source_name}: {player.name} non può accumulare {cost} Peccato senza perdere e la carta viene distrutta."
                )
                engine.send_to_graveyard(owner_idx, source_uid)

            return

        if action == "mill_cards":
            target = self._resolve_player_scope(owner_idx, effect.target_player or "opponent")
            player = engine.state.players[target]
            for _ in range(max(0, int(effect.amount))):
                if not player.deck:
                    break
                uid = player.deck.pop()
                player.graveyard.append(uid)
                self._shuffle_graveyard_if_oltretomba_active(engine, target)
            return
        if action == "draw_cards":
            target = self._resolve_player_scope(owner_idx, effect.target_player)
            engine.draw_cards(target, max(0, int(effect.amount or 1)))
            return

        if action == "choose_option":
            flags = engine.state.flags
            choice_source = str(flags.get("_runtime_choice_source", "")).strip()
            choice_ready = bool(flags.get("_runtime_choice_ready"))

            valid_options: list[dict[str, str]] = []
            for raw_opt in effect.choice_options:
                value = str(raw_opt.get("value", "")).strip()
                if not value:
                    continue
                label = str(raw_opt.get("label", value)).strip() or value
                cond = raw_opt.get("condition", {}) or {}
                if cond:
                    ok = self._eval_condition_node(
                        RuleEventContext(
                            engine=engine,
                            event="on_activate",
                            player_idx=owner_idx,
                            payload={"card": source_uid},
                        ),
                        owner_idx,
                        dict(cond),
                    )
                    if not ok:
                        continue
                valid_options.append({"value": value, "label": label})

            if choice_ready and choice_source == source_uid:
                selected_raw = str(flags.get("_runtime_choice_selected", "")).strip()
                allowed = {opt["value"] for opt in valid_options}
                flags["_runtime_selected_option"] = selected_raw if selected_raw in allowed else ""
                for key in (
                    "_runtime_choice_source",
                    "_runtime_choice_ready",
                    "_runtime_choice_selected",
                    "_runtime_choice_values",
                    "_runtime_choice_labels",
                    "_runtime_choice_owner",
                    "_runtime_choice_title",
                    "_runtime_choice_prompt",
                    "_runtime_choice_min_targets",
                    "_runtime_choice_max_targets",
                ):
                    flags.pop(key, None)
                return

            if not valid_options:
                flags["_runtime_selected_option"] = ""
                return

            flags["_runtime_choice_source"] = source_uid
            flags["_runtime_choice_values"] = ";;".join(opt["value"] for opt in valid_options)
            flags["_runtime_choice_labels"] = json.dumps(
                {opt["value"]: opt["label"] for opt in valid_options},
                ensure_ascii=False,
            )
            flags["_runtime_choice_owner"] = str(owner_idx)
            flags["_runtime_choice_title"] = str(effect.choice_title or "Scegli un'opzione")
            flags["_runtime_choice_prompt"] = str(effect.choice_prompt or "Scegli una modalità.")
            flags["_runtime_choice_min_targets"] = "1"
            flags["_runtime_choice_max_targets"] = "1"
            flags["_runtime_choice_ready"] = False
            flags["_runtime_resume_same_action"] = True
            flags["_runtime_reveal_card"] = source_uid
            flags["_runtime_waiting_for_reveal"] = True
            return

        if action == "choose_draw_amount_with_self_sin_cost":
            flags = engine.state.flags
            target = self._resolve_player_scope(owner_idx, effect.target_player or "me")
            player = engine.state.players[target]
            per_card_sin = max(1, int(effect.amount or 15))
            max_safe_draw = max(0, (99 - int(player.sin)) // per_card_sin)

            choice_source = str(flags.get("_runtime_choice_source", "")).strip()
            choice_ready = bool(flags.get("_runtime_choice_ready"))

            if choice_ready and choice_source == source_uid:
                selected_raw = str(flags.get("_runtime_choice_selected", "")).strip()
                try:
                    requested = int(selected_raw)
                except ValueError:
                    requested = 0
                requested = max(0, min(requested, max_safe_draw))

                drawn = 0
                if requested > 0:
                    drawn = int(engine.draw_cards(target, requested))
                if drawn > 0:
                    engine.gain_sin(target, drawn * per_card_sin)

                for key in (
                    "_runtime_choice_source",
                    "_runtime_choice_ready",
                    "_runtime_choice_selected",
                    "_runtime_choice_values",
                    "_runtime_choice_labels",
                    "_runtime_choice_owner",
                    "_runtime_choice_title",
                    "_runtime_choice_prompt",
                    "_runtime_choice_min_targets",
                    "_runtime_choice_max_targets",
                ):
                    flags.pop(key, None)
                return

            values = [str(n) for n in range(max_safe_draw + 1)]
            labels_map = {str(n): (f"{n} carta" if n == 1 else f"{n} carte") for n in range(max_safe_draw + 1)}
            flags["_runtime_choice_source"] = source_uid
            flags["_runtime_choice_values"] = ";;".join(values)
            flags["_runtime_choice_labels"] = json.dumps(labels_map, ensure_ascii=False)
            flags["_runtime_choice_owner"] = str(owner_idx)
            flags["_runtime_choice_title"] = str(effect.choice_title or "Scegli quante carte pescare")
            flags["_runtime_choice_prompt"] = str(
                effect.choice_prompt
                or f"Puoi pescare da 0 a {max_safe_draw} carte senza perdere per Peccato."
            )
            flags["_runtime_choice_min_targets"] = "1"
            flags["_runtime_choice_max_targets"] = "1"
            flags["_runtime_choice_ready"] = False
            flags["_runtime_resume_same_action"] = True
            flags["_runtime_reveal_card"] = source_uid
            flags["_runtime_waiting_for_reveal"] = True
            return

        if action == "choose_targets":
            flags = engine.state.flags
            choice_source = str(flags.get("_runtime_choice_source", "")).strip()
            choice_ready = bool(flags.get("_runtime_choice_ready"))
            min_targets = max(0, int(effect.min_targets if effect.min_targets is not None else 0))
            max_targets = int(effect.max_targets if effect.max_targets is not None else 1)
            max_targets = max(min_targets, max_targets)

            if choice_ready and choice_source == source_uid:
                selected_raw = str(flags.get("_runtime_choice_selected", "")).strip()
                candidates_raw = str(flags.get("_runtime_choice_candidates", "")).strip()
                candidates = [v for v in candidates_raw.split(";;") if v]
                selected_uids = [v.strip() for v in selected_raw.split(",") if v.strip()]
                selected_uids = [uid for uid in selected_uids if uid in candidates]
                if max_targets >= 0:
                    selected_uids = selected_uids[:max_targets]
                if len(selected_uids) < min_targets:
                    selected_uids = []
                flags["_runtime_selected_target"] = ",".join(selected_uids)
                for key in (
                    "_runtime_choice_source",
                    "_runtime_choice_ready",
                    "_runtime_choice_selected",
                    "_runtime_choice_candidates",
                    "_runtime_choice_owner",
                    "_runtime_choice_title",
                    "_runtime_choice_prompt",
                    "_runtime_choice_min_targets",
                    "_runtime_choice_max_targets",
                ):
                    flags.pop(key, None)
                return

            candidates = list(targets)
            if not candidates:
                flags["_runtime_selected_target"] = ""
                return
            flags["_runtime_choice_source"] = source_uid
            flags["_runtime_choice_candidates"] = ";;".join(candidates)
            flags["_runtime_choice_owner"] = str(owner_idx)
            flags["_runtime_choice_title"] = "Selezione Bersaglio"
            flags["_runtime_choice_prompt"] = "Seleziona i bersagli per l'effetto."
            flags["_runtime_choice_min_targets"] = str(min_targets)
            flags["_runtime_choice_max_targets"] = str(max_targets)
            flags["_runtime_choice_ready"] = False
            flags["_runtime_resume_same_action"] = True
            flags["_runtime_reveal_card"] = source_uid
            flags["_runtime_waiting_for_reveal"] = True
            return
        if action == "sacrifice_time_resolution":
            flags = engine.state.flags
            owner_player = engine.state.players[owner_idx]
            opponent_idx = 1 - owner_idx
            opponent_player = engine.state.players[opponent_idx]
            state_key = f"_sacrifice_time_state_{source_uid}"
            local_state = dict(flags.get(state_key, {}) or {})
            pending = int(local_state.get("pending", 0))

            choice_source = str(flags.get("_runtime_choice_source", "")).strip()
            choice_ready = bool(flags.get("_runtime_choice_ready"))

            if not local_state:
                discarded_count = 0
                for hand_uid in list(owner_player.hand):
                    owner_player.hand.remove(hand_uid)
                    if hand_uid not in owner_player.graveyard:
                        owner_player.graveyard.append(hand_uid)
                        self._shuffle_graveyard_if_oltretomba_active(engine, owner_idx)
                    discarded_count += 1
                    engine._emit_event(
                        "on_card_discarded",
                        owner_idx,
                        card=hand_uid,
                        from_hand_to_graveyard=True,
                    )
                    engine._emit_event(
                        "on_card_sent_to_graveyard",
                        owner_idx,
                        card=hand_uid,
                        from_zone="hand",
                        owner=owner_idx,
                    )
                    self._maybe_auto_activate_discarded_from_hand_by_effect(engine, owner_idx, hand_uid, source_uid)
                pending = discarded_count

            if pending <= 0:
                flags.pop(state_key, None)
                return

            if choice_ready and choice_source == source_uid:
                mode = str(local_state.get("mode", "")).strip()
                selected_raw = str(flags.get("_runtime_choice_selected", "")).strip()
                candidates_raw = str(flags.get("_runtime_choice_candidates", "")).strip()
                candidates = [v for v in candidates_raw.split(";;") if v]
                selected_uids = [v.strip() for v in selected_raw.split(",") if v.strip()]
                selected_uids = [uid for uid in selected_uids if uid in candidates]

                if mode == "field":
                    for t_uid in selected_uids:
                        if t_uid in engine.state.instances:
                            engine.send_to_graveyard(engine.state.instances[t_uid].owner, t_uid)
                    pending = max(0, pending - len(selected_uids))
                elif mode == "hand":
                    for t_uid in selected_uids:
                        if t_uid in opponent_player.hand:
                            opponent_player.hand.remove(t_uid)
                            if t_uid not in opponent_player.graveyard:
                                opponent_player.graveyard.append(t_uid)
                                self._shuffle_graveyard_if_oltretomba_active(engine, opponent_idx)
                            pending = max(0, pending - 1)
                            engine._emit_event(
                                "on_card_discarded",
                                opponent_idx,
                                card=t_uid,
                                from_hand_to_graveyard=True,
                            )
                            engine._emit_event(
                                "on_card_sent_to_graveyard",
                                opponent_idx,
                                card=t_uid,
                                from_zone="hand",
                                owner=opponent_idx,
                            )
                            self._maybe_auto_activate_discarded_from_hand_by_effect(engine, opponent_idx, t_uid, source_uid)

                for key in (
                    "_runtime_choice_source",
                    "_runtime_choice_ready",
                    "_runtime_choice_selected",
                    "_runtime_choice_candidates",
                    "_runtime_choice_owner",
                    "_runtime_choice_title",
                    "_runtime_choice_prompt",
                    "_runtime_choice_min_targets",
                    "_runtime_choice_max_targets",
                ):
                    flags.pop(key, None)

            enemy_field: list[str] = []
            for uid in opponent_player.attack + opponent_player.defense + opponent_player.artifacts:
                if uid:
                    enemy_field.append(uid)
            if opponent_player.building:
                enemy_field.append(opponent_player.building)

            if pending > 0 and enemy_field:
                max_pick = min(pending, len(enemy_field))
                flags[state_key] = {"pending": pending, "mode": "field"}
                flags["_runtime_choice_source"] = source_uid
                flags["_runtime_choice_candidates"] = ";;".join(enemy_field)
                flags["_runtime_choice_owner"] = str(owner_idx)
                flags["_runtime_choice_title"] = "Sacrificio del Tempo"
                flags["_runtime_choice_prompt"] = "Seleziona le carte avversarie sul terreno da inviare al cimitero."
                flags["_runtime_choice_min_targets"] = str(max_pick)
                flags["_runtime_choice_max_targets"] = str(max_pick)
                flags["_runtime_choice_ready"] = False
                flags["_runtime_resume_same_action"] = True
                flags["_runtime_reveal_card"] = source_uid
                flags["_runtime_waiting_for_reveal"] = True
                return

            if pending > 0 and opponent_player.hand:
                max_pick = min(pending, len(opponent_player.hand))
                flags[state_key] = {"pending": pending, "mode": "hand"}
                flags["_runtime_choice_source"] = source_uid
                flags["_runtime_choice_candidates"] = ";;".join(opponent_player.hand)
                flags["_runtime_choice_owner"] = str(owner_idx)
                flags["_runtime_choice_title"] = "Sacrificio del Tempo"
                flags["_runtime_choice_prompt"] = "Seleziona le carte della mano avversaria da scartare."
                flags["_runtime_choice_min_targets"] = str(max_pick)
                flags["_runtime_choice_max_targets"] = str(max_pick)
                flags["_runtime_choice_ready"] = False
                flags["_runtime_resume_same_action"] = True
                flags["_runtime_reveal_card"] = source_uid
                flags["_runtime_waiting_for_reveal"] = True
                return

            while pending > 0 and opponent_player.deck:
                top_uid = opponent_player.deck.pop()
                if top_uid not in opponent_player.graveyard:
                    opponent_player.graveyard.append(top_uid)
                    self._shuffle_graveyard_if_oltretomba_active(engine, opponent_idx)
                pending -= 1
                engine._emit_event(
                    "on_card_sent_to_graveyard",
                    opponent_idx,
                    card=top_uid,
                    from_zone="relicario",
                    owner=opponent_idx,
                )

            if pending > 0 and not opponent_player.deck:
                flags.pop(state_key, None)
                engine.state.winner = owner_idx
                engine.state.game_over = True
                engine.state.log(f"{owner_player.name} vince per effetto di Sacrificio del Tempo.")
                return

            if pending > 0:
                flags[state_key] = {"pending": pending}
                flags["_runtime_resume_same_action"] = True
                return

            flags.pop(state_key, None)
            return
        if action == "discard_hand_then_pressure_opponent":
            flags = engine.state.flags
            owner_player = engine.state.players[owner_idx]
            target_idx = self._resolve_player_scope(owner_idx, effect.target_player or "opponent")
            target_player = engine.state.players[target_idx]
            per_card_amount = max(1, int(effect.amount or 1))

            state_key = f"_runtime_pressure_state_{source_uid}"
            local_state = dict(flags.get(state_key, {}) or {})
            pending = int(local_state.get("pending", 0))

            choice_source = str(flags.get("_runtime_choice_source", "")).strip()
            choice_ready = bool(flags.get("_runtime_choice_ready"))

            if not local_state:
                discarded_count = 0
                for hand_uid in list(owner_player.hand):
                    owner_player.hand.remove(hand_uid)
                    if hand_uid not in owner_player.graveyard:
                        owner_player.graveyard.append(hand_uid)
                        self._shuffle_graveyard_if_oltretomba_active(engine, owner_idx)
                    discarded_count += 1
                    engine._emit_event(
                        "on_card_discarded",
                        owner_idx,
                        card=hand_uid,
                        from_hand_to_graveyard=True,
                    )
                    engine._emit_event(
                        "on_card_sent_to_graveyard",
                        owner_idx,
                        card=hand_uid,
                        from_zone="hand",
                        owner=owner_idx,
                    )
                    self._maybe_auto_activate_discarded_from_hand_by_effect(engine, owner_idx, hand_uid, source_uid)
                pending = discarded_count * per_card_amount

            if pending <= 0:
                flags.pop(state_key, None)
                return

            if choice_ready and choice_source == source_uid:
                mode = str(local_state.get("mode", "")).strip()
                selected_raw = str(flags.get("_runtime_choice_selected", "")).strip()
                candidates_raw = str(flags.get("_runtime_choice_candidates", "")).strip()
                candidates = [v for v in candidates_raw.split(";;") if v]
                selected_uids = [v.strip() for v in selected_raw.split(",") if v.strip()]
                selected_uids = [uid for uid in selected_uids if uid in candidates]

                if mode == "field":
                    for t_uid in selected_uids:
                        if t_uid in engine.state.instances:
                            engine.send_to_graveyard(engine.state.instances[t_uid].owner, t_uid)
                    pending = max(0, pending - len(selected_uids))
                elif mode == "hand":
                    for t_uid in selected_uids:
                        if t_uid in target_player.hand:
                            target_player.hand.remove(t_uid)
                            if t_uid not in target_player.graveyard:
                                target_player.graveyard.append(t_uid)
                                self._shuffle_graveyard_if_oltretomba_active(engine, target_idx)
                            pending = max(0, pending - 1)
                            engine._emit_event(
                                "on_card_discarded",
                                target_idx,
                                card=t_uid,
                                from_hand_to_graveyard=True,
                            )
                            engine._emit_event(
                                "on_card_sent_to_graveyard",
                                target_idx,
                                card=t_uid,
                                from_zone="hand",
                                owner=target_idx,
                            )
                            self._maybe_auto_activate_discarded_from_hand_by_effect(engine, target_idx, t_uid, source_uid)

                for key in (
                    "_runtime_choice_source",
                    "_runtime_choice_ready",
                    "_runtime_choice_selected",
                    "_runtime_choice_candidates",
                    "_runtime_choice_owner",
                    "_runtime_choice_title",
                    "_runtime_choice_prompt",
                    "_runtime_choice_min_targets",
                    "_runtime_choice_max_targets",
                ):
                    flags.pop(key, None)

            target_field: list[str] = []
            for uid in target_player.attack + target_player.defense + target_player.artifacts:
                if uid:
                    target_field.append(uid)
            if target_player.building:
                target_field.append(target_player.building)

            if pending > 0 and target_field:
                max_pick = min(pending, len(target_field))
                flags[state_key] = {"pending": pending, "mode": "field"}
                flags["_runtime_choice_source"] = source_uid
                flags["_runtime_choice_candidates"] = ";;".join(target_field)
                flags["_runtime_choice_owner"] = str(owner_idx)
                flags["_runtime_choice_title"] = str(effect.choice_title or "Selezione Bersagli")
                flags["_runtime_choice_prompt"] = str(
                    effect.choice_prompt or "Seleziona le carte sul terreno da inviare al cimitero."
                )
                flags["_runtime_choice_min_targets"] = str(max_pick)
                flags["_runtime_choice_max_targets"] = str(max_pick)
                flags["_runtime_choice_ready"] = False
                flags["_runtime_resume_same_action"] = True
                flags["_runtime_reveal_card"] = source_uid
                flags["_runtime_waiting_for_reveal"] = True
                return

            if pending > 0 and target_player.hand:
                max_pick = min(pending, len(target_player.hand))
                flags[state_key] = {"pending": pending, "mode": "hand"}
                flags["_runtime_choice_source"] = source_uid
                flags["_runtime_choice_candidates"] = ";;".join(target_player.hand)
                flags["_runtime_choice_owner"] = str(owner_idx)
                flags["_runtime_choice_title"] = str(effect.choice_title or "Selezione Bersagli")
                flags["_runtime_choice_prompt"] = str(effect.choice_prompt or "Seleziona le carte dalla mano da scartare.")
                flags["_runtime_choice_min_targets"] = str(max_pick)
                flags["_runtime_choice_max_targets"] = str(max_pick)
                flags["_runtime_choice_ready"] = False
                flags["_runtime_resume_same_action"] = True
                flags["_runtime_reveal_card"] = source_uid
                flags["_runtime_waiting_for_reveal"] = True
                return

            while pending > 0 and target_player.deck:
                top_uid = target_player.deck.pop()
                if top_uid not in target_player.graveyard:
                    target_player.graveyard.append(top_uid)
                    self._shuffle_graveyard_if_oltretomba_active(engine, target_idx)
                pending -= 1
                engine._emit_event(
                    "on_card_sent_to_graveyard",
                    target_idx,
                    card=top_uid,
                    from_zone="relicario",
                    owner=target_idx,
                )

            if pending > 0 and not target_player.deck:
                flags.pop(state_key, None)
                engine.state.winner = owner_idx
                engine.state.game_over = True
                source_name = engine.state.instances[source_uid].definition.name if source_uid in engine.state.instances else source_uid
                engine.state.log(f"{owner_player.name} vince per effetto di {source_name}.")
                return

            if pending > 0:
                flags[state_key] = {"pending": pending}
                flags["_runtime_resume_same_action"] = True
                return

            flags.pop(state_key, None)
            return
        if action == "store_target_count":
            flag_name = str(effect.flag or "").strip()
            if not flag_name:
                return
            engine.state.flags[flag_name] = int(len(targets))
            return
        if action == "add_link_tag_to_source_from_selected_target":
            source_inst = engine.state.instances.get(source_uid)
            if source_inst is None:
                return
            tag_prefix = str(effect.flag or "link").strip() or "link"
            for t_uid in targets:
                if t_uid not in engine.state.instances:
                    continue
                link_tag = f"{tag_prefix}:{t_uid}"
                if link_tag not in source_inst.blessed:
                    source_inst.blessed.append(link_tag)
            return
        if action == "destroy_linked_targets_from_source_tags":
            source_inst = engine.state.instances.get(source_uid)
            if source_inst is None:
                return
            tag_prefix = str(effect.flag or "link").strip() or "link"
            to_destroy: list[str] = []
            for tag in list(source_inst.blessed):
                if not isinstance(tag, str) or not tag.startswith(f"{tag_prefix}:"):
                    continue
                linked_uid = tag.split(":", 1)[1].strip()
                if linked_uid and linked_uid in engine.state.instances:
                    to_destroy.append(linked_uid)
            for linked_uid in to_destroy:
                linked_inst = engine.state.instances.get(linked_uid)
                if linked_inst is None:
                    continue
                engine.destroy_any_card(linked_inst.owner, linked_uid)
            source_inst.blessed = [
                tag
                for tag in source_inst.blessed
                if not (isinstance(tag, str) and tag.startswith(f"{tag_prefix}:"))
            ]
            return
        if action == "move_all_from_zone_to_zone":
            from_zone = _norm(effect.from_zone or effect.zone or "")
            to_zone = str(effect.to_zone or "").strip()
            if not from_zone or not to_zone:
                return
            target = self._resolve_player_scope(owner_idx, effect.target_player or "me")
            player = engine.state.players[target]
            if from_zone == "graveyard":
                pool = list(player.graveyard)
            elif from_zone in {"deck", "relicario"}:
                pool = list(player.deck)
            elif from_zone == "hand":
                pool = list(player.hand)
            elif from_zone == "excommunicated":
                pool = list(player.excommunicated)
            elif from_zone == "field":
                pool = [uid for uid in (player.attack + player.defense + player.artifacts) if uid]
                if player.building:
                    pool.append(player.building)
            else:
                pool = []
            for uid in pool:
                self._move_uid_to_zone(engine, uid, to_zone, target)
            if bool(effect.shuffle_after):
                engine.rng.shuffle(player.deck)
            return
        if action == "activate_oltretomba_promise":
            flags = engine.state.flags
            promise_state = dict(flags.get("oltretomba_promise_active", {"0": False, "1": False}) or {"0": False, "1": False})
            promise_state[str(owner_idx)] = True
            flags["oltretomba_promise_active"] = promise_state

            player = engine.state.players[owner_idx]
            for uid in list(player.deck):
                if uid not in player.graveyard:
                    player.graveyard.append(uid)
            player.deck = []
            engine.rng.shuffle(player.graveyard)
            engine.state.log("Promessa dell'oltretomba attiva: reliquiario e cimitero diventano la stessa zona.")
            return
        if action == "floor_divide_flag":
            flag_name = str(effect.flag or "").strip()
            if not flag_name:
                return
            divisor = max(1, int(effect.amount or 1))
            raw_value = engine.state.flags.get(flag_name, 0)
            try:
                value = int(raw_value)
            except (TypeError, ValueError):
                value = 0
            engine.state.flags[flag_name] = max(0, value // divisor)
            return
        if action == "draw_cards_from_flag":
            flag_name = str(effect.flag or "").strip()
            if not flag_name:
                return
            raw_value = engine.state.flags.get(flag_name, 0)
            try:
                amount = max(0, int(raw_value))
            except (TypeError, ValueError):
                amount = 0
            target = self._resolve_player_scope(owner_idx, effect.target_player or "me")
            if amount > 0:
                engine.draw_cards(target, amount)
            engine.state.flags.pop(flag_name, None)
            return
        if action == "optional_draw_from_top_n_then_shuffle":
            top_n = max(1, int(effect.amount or 1))
            target = self._resolve_player_scope(owner_idx, effect.target_player or "me")
            player = engine.state.players[target]
            flags = engine.state.flags

            choice_source = str(flags.get("_runtime_choice_source", "")).strip()
            choice_ready = bool(flags.get("_runtime_choice_ready"))
            if choice_ready and choice_source == source_uid:
                selected_uid = str(flags.get("_runtime_choice_selected", "")).strip()
                candidates_raw = str(flags.get("_runtime_choice_candidates", "")).strip()
                candidates = [v for v in candidates_raw.split(";;") if v]
                if selected_uid and selected_uid in candidates and selected_uid in player.deck:
                    self._move_uid_to_zone(engine, selected_uid, "hand", target)
                engine.rng.shuffle(player.deck)
                for key in (
                    "_runtime_choice_source",
                    "_runtime_choice_ready",
                    "_runtime_choice_selected",
                    "_runtime_choice_candidates",
                    "_runtime_choice_owner",
                    "_runtime_choice_title",
                    "_runtime_choice_prompt",
                    "_runtime_choice_min_targets",
                    "_runtime_choice_max_targets",
                ):
                    flags.pop(key, None)
                return

            candidates = list(player.deck[-top_n:]) if player.deck else []
            flags["_runtime_choice_source"] = source_uid
            flags["_runtime_choice_candidates"] = ";;".join(candidates)
            flags["_runtime_choice_owner"] = str(target)
            flags["_runtime_choice_title"] = "Scegli Carta"
            flags["_runtime_choice_prompt"] = "Scegli una carta tra le prime del reliquiario oppure Nessuna."
            flags["_runtime_choice_min_targets"] = "0"
            flags["_runtime_choice_max_targets"] = "1"
            flags["_runtime_choice_ready"] = False
            flags["_runtime_resume_same_action"] = True
            flags["_runtime_reveal_card"] = source_uid
            flags["_runtime_waiting_for_reveal"] = True
            return
        if action == "reorder_top_n_of_deck":
            top_n = max(1, int(effect.amount or 1))
            target = self._resolve_player_scope(owner_idx, effect.target_player or "me")
            player = engine.state.players[target]
            flags = engine.state.flags

            choice_source = str(flags.get("_runtime_choice_source", "")).strip()
            choice_ready = bool(flags.get("_runtime_choice_ready"))

            if choice_ready and choice_source == source_uid:
                selected_raw = str(flags.get("_runtime_choice_selected", "")).strip()
                candidates_raw = str(flags.get("_runtime_choice_candidates", "")).strip()

                candidates = [v for v in candidates_raw.split(";;") if v]
                selected_uids = [v.strip() for v in selected_raw.split(",") if v.strip()]
                selected_uids = [uid for uid in selected_uids if uid in candidates]

                if len(selected_uids) == len(candidates) and candidates:
                    base_deck = list(player.deck[:-len(candidates)])
                    # selected_uids = ordine desiderato dall'alto verso il basso
                    player.deck = base_deck + list(reversed(selected_uids))

                for key in (
                    "_runtime_choice_source",
                    "_runtime_choice_ready",
                    "_runtime_choice_selected",
                    "_runtime_choice_candidates",
                    "_runtime_choice_owner",
                    "_runtime_choice_title",
                    "_runtime_choice_prompt",
                    "_runtime_choice_min_targets",
                    "_runtime_choice_max_targets",
                    "_runtime_choice_preserve_order",
                ):
                    flags.pop(key, None)
                return

            candidates = list(reversed(player.deck[-top_n:])) if player.deck else []
            if not candidates:
                return

            flags["_runtime_choice_source"] = source_uid
            flags["_runtime_choice_candidates"] = ";;".join(candidates)
            flags["_runtime_choice_owner"] = str(target)
            flags["_runtime_choice_title"] = "Riordina le carte"
            flags["_runtime_choice_prompt"] = "Seleziona tutte le carte nell'ordine desiderato, dalla prima che vuoi in cima alla quinta."
            flags["_runtime_choice_min_targets"] = str(len(candidates))
            flags["_runtime_choice_max_targets"] = str(len(candidates))
            flags["_runtime_choice_preserve_order"] = True
            flags["_runtime_choice_ready"] = False
            flags["_runtime_resume_same_action"] = True
            flags["_runtime_reveal_card"] = source_uid
            flags["_runtime_waiting_for_reveal"] = True
            return
        if action == "optional_recover_from_graveyard_then_shuffle":
            target = self._resolve_player_scope(owner_idx, effect.target_player or "me")
            player = engine.state.players[target]
            flags = engine.state.flags

            choice_source = str(flags.get("_runtime_choice_source", "")).strip()
            choice_ready = bool(flags.get("_runtime_choice_ready"))
            if choice_ready and choice_source == source_uid:
                selected_uid = str(flags.get("_runtime_choice_selected", "")).strip()
                candidates_raw = str(flags.get("_runtime_choice_candidates", "")).strip()
                candidates = [v for v in candidates_raw.split(";;") if v]
                if selected_uid and selected_uid in candidates and selected_uid in player.graveyard:
                    has_odino = any(
                        _norm(engine.state.instances[uid].definition.name) == _norm("Odino")
                        for uid in engine.all_saints_on_field(target)
                    )
                    to_zone = "hand" if has_odino else "relicario"
                    moved = self._move_uid_to_zone(engine, selected_uid, to_zone, target)
                    if not moved and to_zone == "hand":
                        self._move_uid_to_zone(engine, selected_uid, "relicario", target)
                engine.rng.shuffle(player.deck)
                for key in (
                    "_runtime_choice_source",
                    "_runtime_choice_ready",
                    "_runtime_choice_selected",
                    "_runtime_choice_candidates",
                    "_runtime_choice_owner",
                    "_runtime_choice_title",
                    "_runtime_choice_prompt",
                    "_runtime_choice_min_targets",
                    "_runtime_choice_max_targets",
                ):
                    flags.pop(key, None)
                return

            candidates = list(player.graveyard)
            if not candidates:
                engine.rng.shuffle(player.deck)
                return
            has_odino = any(
                _norm(engine.state.instances[uid].definition.name) == _norm("Odino")
                for uid in engine.all_saints_on_field(target)
            )
            flags["_runtime_choice_source"] = source_uid
            flags["_runtime_choice_candidates"] = ";;".join(candidates)
            flags["_runtime_choice_owner"] = str(target)
            flags["_runtime_choice_title"] = "Cimitero"
            if has_odino:
                flags["_runtime_choice_prompt"] = "Scegli una carta dal tuo cimitero da aggiungere alla mano, oppure Nessuna."
            else:
                flags["_runtime_choice_prompt"] = "Scegli una carta dal tuo cimitero da mettere nel reliquiario, oppure Nessuna."
            flags["_runtime_choice_min_targets"] = "0"
            flags["_runtime_choice_max_targets"] = "1"
            flags["_runtime_choice_ready"] = False
            flags["_runtime_resume_same_action"] = True
            flags["_runtime_reveal_card"] = source_uid
            flags["_runtime_waiting_for_reveal"] = True
            return
        if action == "optional_recover_cards":
            target = self._resolve_player_scope(owner_idx, effect.target_player or "me")
            player = engine.state.players[target]
            flags = engine.state.flags

            from_zone = _norm(effect.from_zone or effect.zone or "graveyard")
            to_zone = str(effect.to_zone or "relicario").strip() or "relicario"
            min_targets = max(0, int(effect.min_targets if effect.min_targets is not None else 0))
            max_targets = int(effect.max_targets if effect.max_targets is not None else 1)
            max_targets = max(min_targets, max_targets)

            choice_source = str(flags.get("_runtime_choice_source", "")).strip()
            choice_ready = bool(flags.get("_runtime_choice_ready"))
            if choice_ready and choice_source == source_uid:
                selected_raw = str(flags.get("_runtime_choice_selected", "")).strip()
                candidates_raw = str(flags.get("_runtime_choice_candidates", "")).strip()
                candidates = [v for v in candidates_raw.split(";;") if v]
                selected_uids = [v.strip() for v in selected_raw.split(",") if v.strip()]
                selected_uids = [uid for uid in selected_uids if uid in candidates]
                if max_targets >= 0:
                    selected_uids = selected_uids[:max_targets]

                actual_to_zone = to_zone
                generic_cond = effect.to_zone_if_condition if isinstance(effect.to_zone_if_condition, dict) else None
                generic_to_zone = str(effect.to_zone_if or "").strip()
                if generic_cond and generic_to_zone:
                    cond_ctx = RuleEventContext(engine=engine, event="on_effect", player_idx=target, payload={"card": source_uid})
                    if self._eval_condition_node(cond_ctx, target, generic_cond):
                        actual_to_zone = generic_to_zone
                else:
                    condition_name = _norm(effect.controller_has_saint_with_name or "")
                    conditional_to = str(effect.to_zone_if_controller_has_saint_with_name or "").strip()
                    if condition_name and conditional_to:
                        has_required = any(
                            _card_matches_name(engine.state.instances[uid].definition, condition_name)
                            for uid in engine.all_saints_on_field(target)
                        )
                        actual_to_zone = conditional_to if has_required else to_zone

                for selected_uid in selected_uids:
                    still_available = selected_uid in self._get_zone_cards(engine, target, from_zone)
                    if not still_available:
                        continue
                    moved = self._move_uid_to_zone(engine, selected_uid, actual_to_zone, target)
                    if not moved and _norm(actual_to_zone) == "hand":
                        self._move_uid_to_zone(engine, selected_uid, "relicario", target)

                if effect.shuffle_after:
                    engine.rng.shuffle(player.deck)
                for key in (
                    "_runtime_choice_source",
                    "_runtime_choice_ready",
                    "_runtime_choice_selected",
                    "_runtime_choice_candidates",
                    "_runtime_choice_owner",
                    "_runtime_choice_title",
                    "_runtime_choice_prompt",
                    "_runtime_choice_min_targets",
                    "_runtime_choice_max_targets",
                ):
                    flags.pop(key, None)
                return

            candidates = self._get_zone_cards(engine, target, from_zone)
            if not candidates:
                if effect.shuffle_after:
                    engine.rng.shuffle(player.deck)
                return

            default_title = "Scegli Carta"
            if from_zone == "graveyard":
                default_title = "Cimitero"
            flags["_runtime_choice_source"] = source_uid
            flags["_runtime_choice_candidates"] = ";;".join(candidates)
            flags["_runtime_choice_owner"] = str(target)
            flags["_runtime_choice_title"] = default_title
            flags["_runtime_choice_prompt"] = (
                f"Scegli da {from_zone} una o piu carte (min {min_targets}, max {max_targets}) oppure Nessuna."
            )
            flags["_runtime_choice_min_targets"] = str(min_targets)
            flags["_runtime_choice_max_targets"] = str(max_targets)
            flags["_runtime_choice_ready"] = False
            flags["_runtime_resume_same_action"] = True
            flags["_runtime_reveal_card"] = source_uid
            flags["_runtime_waiting_for_reveal"] = True
            return
        if action == "inflict_sin":
            target = self._resolve_player_scope(owner_idx, effect.target_player or "opponent")
            engine.gain_sin(target, max(0, int(effect.amount)))
            return
        if action == "inflict_sin_from_source_paid_inspiration":
            source_inst = engine.state.instances.get(source_uid)
            if source_inst is None:
                return
            amount = 0
            for tag in list(source_inst.blessed):
                if not isinstance(tag, str) or not tag.startswith("paid_inspiration_on_summon:"):
                    continue
                try:
                    amount = max(0, int(tag.split(":", 1)[1]))
                except (TypeError, ValueError):
                    amount = 0
                break
            if amount <= 0:
                return
            target = self._resolve_player_scope(owner_idx, effect.target_player or "opponent")
            engine.gain_sin(target, amount)
            return
        if action == "inflict_sin_from_flag":
            flag_name = str(effect.flag or "").strip()
            if not flag_name:
                return

            raw_value = engine.state.flags.get(flag_name, 0)
            try:
                amount = int(raw_value)
            except (TypeError, ValueError):
                amount = 0

            if amount <= 0:
                engine.state.flags.pop(flag_name, None)
                return

            target = self._resolve_player_scope(owner_idx, effect.target_player or "opponent")
            engine.gain_sin(target, amount)
            engine.state.flags.pop(flag_name, None)
            return
        if action == "inflict_sin_to_target_owners":
            per_card = max(0, int(effect.amount))
            if per_card <= 0:
                return
            counts: dict[int, int] = {}
            for t_uid in targets:
                inst = engine.state.instances.get(t_uid)
                if inst is None:
                    continue
                counts[inst.owner] = int(counts.get(inst.owner, 0)) + 1
            for p_idx, qty in counts.items():
                if qty > 0:
                    engine.gain_sin(p_idx, per_card * qty)
            return
        if action == "remove_sin":
            target = self._resolve_player_scope(owner_idx, effect.target_player or "me")
            engine.reduce_sin(target, max(0, int(effect.amount)))
            return
        if action == "remove_sin_from_flag":
            flag_name = str(effect.flag or "").strip()
            if not flag_name:
                return
            raw_value = engine.state.flags.get(flag_name, 0)
            try:
                amount = max(0, int(raw_value))
            except (TypeError, ValueError):
                amount = 0
            target = self._resolve_player_scope(owner_idx, effect.target_player or "me")
            if amount > 0:
                engine.reduce_sin(target, amount)
            engine.state.flags.pop(flag_name, None)
            return
        if action == "increase_faith_from_flag":
            flag_name = str(effect.flag or "").strip()
            if not flag_name:
                return
            raw_value = engine.state.flags.get(flag_name, 0)
            try:
                amount = int(raw_value)
            except (TypeError, ValueError):
                amount = 0
            if amount <= 0:
                engine.state.flags.pop(flag_name, None)
                return
            for t_uid in targets:
                inst = engine.state.instances.get(t_uid)
                if inst is None:
                    continue
                inst.current_faith = int(inst.current_faith or 0) + amount
            engine.state.flags.pop(flag_name, None)
            return
        if action == "decrease_faith_from_flag":
            flag_name = str(effect.flag or "").strip()
            if not flag_name:
                return
            raw_value = engine.state.flags.get(flag_name, 0)
            try:
                amount = max(0, int(raw_value))
            except (TypeError, ValueError):
                amount = 0
            if amount <= 0:
                engine.state.flags.pop(flag_name, None)
                return
            for t_uid in targets:
                inst = engine.state.instances.get(t_uid)
                if inst is None:
                    continue
                current = int(inst.current_faith or 0)
                inst.current_faith = current - amount
                if _norm(inst.definition.card_type) in {"santo", "token"} and int(inst.current_faith or 0) <= 0:
                    engine.destroy_saint_by_uid(inst.owner, t_uid, cause="effect")
            engine.state.flags.pop(flag_name, None)
            return
        if action == "add_inspiration":
            target = self._resolve_player_scope(owner_idx, effect.target_player or "me")
            player = engine.state.players[target]
            player.inspiration = max(0, int(player.inspiration) + int(effect.amount))
            return
        if action == "destroy_card":
            for t_uid in targets:
                inst = engine.state.instances.get(t_uid)
                if inst is None:
                    continue
                engine.destroy_any_card(inst.owner, t_uid)
            return
        if action == "destroy_all_saints_except_selected":
            required_opponent_selected = max(0, int(effect.min_targets if effect.min_targets is not None else 0))
            selected_set = {
                uid for uid in targets
                if uid in engine.state.instances and _norm(engine.state.instances[uid].definition.card_type) in {"santo", "token"}
            }
            selected_opponent = sum(
                1 for uid in selected_set
                if int(engine.state.instances[uid].owner) != int(owner_idx)
            )
            if selected_opponent < required_opponent_selected:
                engine.state.log("Tornado: selezione non valida, serve almeno un Santo avversario tra i bersagli.")
                return

            to_destroy: list[tuple[int, str]] = []
            for p_idx in (0, 1):
                p = engine.state.players[p_idx]
                for uid in list(p.attack + p.defense):
                    if uid is None:
                        continue
                    if uid in selected_set:
                        continue
                    inst = engine.state.instances.get(uid)
                    if inst is None:
                        continue
                    if _norm(inst.definition.card_type) not in {"santo", "token"}:
                        continue
                    to_destroy.append((inst.owner, uid))

            for real_owner, uid in to_destroy:
                if uid not in engine.state.instances:
                    continue
                engine.destroy_saint_by_uid(real_owner, uid, cause="effect")
            return
        if action == "excommunicate_card":
            for t_uid in targets:
                inst = engine.state.instances.get(t_uid)
                if inst is None:
                    continue
                ctype = _norm(inst.definition.card_type)
                if ctype in {"santo", "token"}:
                    engine.destroy_saint_by_uid(inst.owner, t_uid, excommunicate=True, cause="effect")
                else:
                    engine.excommunicate_card(inst.owner, t_uid)
            return
        if action == "excommunicate_card_no_sin":
            for t_uid in targets:
                inst = engine.state.instances.get(t_uid)
                if inst is None:
                    continue
                engine.excommunicate_card(inst.owner, t_uid)
            return
        if action == "excommunicate_top_cards_from_relicario":
            target = self._resolve_player_scope(owner_idx, effect.target_player or "me")
            count = max(1, int(effect.amount or 1))
            for _ in range(count):
                player = engine.state.players[target]
                if not player.deck:
                    break
                top_uid = player.deck[-1]
                engine.excommunicate_card(target, top_uid, from_zone_override="relicario")
            return
        if action == "remove_from_board_no_sin":
            for t_uid in targets:
                inst = engine.state.instances.get(t_uid)
                if inst is None:
                    continue
                engine.remove_from_board_no_sin(inst.owner, t_uid)
            return
        if action == "move_to_hand":
            for t_uid in targets:
                inst = engine.state.instances.get(t_uid)
                if inst is None:
                    continue
                owner = inst.owner
                moved = self._move_uid_to_zone(engine, t_uid, "hand", owner)
                if moved:
                    engine.state.log(f"{inst.definition.name} viene aggiunta alla mano.")
            return
        if action == "move_first_to_hand":
            for t_uid in targets:
                inst = engine.state.instances.get(t_uid)
                if inst is None:
                    continue
                owner = inst.owner
                moved = self._move_uid_to_zone(engine, t_uid, "hand", owner)
                if moved:
                    engine.state.log(f"{inst.definition.name} viene aggiunta alla mano.")
                break
            return
        if action == "choose_artifact_from_relicario_then_shuffle":
            flags = engine.state.flags
            target = self._resolve_player_scope(owner_idx, effect.target_player or "me")
            player = engine.state.players[target]

            choice_source = str(flags.get("_runtime_choice_source", "")).strip()
            choice_ready = bool(flags.get("_runtime_choice_ready"))
            expected_choice_source = f"{source_uid}:choose_artifact_from_relicario_then_shuffle:{target}"

            if choice_ready and choice_source == expected_choice_source:
                selected_uid = str(flags.get("_runtime_choice_selected", "")).strip()
                candidates_raw = str(flags.get("_runtime_choice_candidates", "")).strip()
                candidates = [v for v in candidates_raw.split(";;") if v]
                if selected_uid in candidates and selected_uid in player.deck:
                    self._move_uid_to_zone(engine, selected_uid, "hand", target)
                engine.rng.shuffle(player.deck)
                for key in (
                    "_runtime_choice_source",
                    "_runtime_choice_ready",
                    "_runtime_choice_selected",
                    "_runtime_choice_candidates",
                    "_runtime_choice_owner",
                    "_runtime_choice_title",
                    "_runtime_choice_prompt",
                    "_runtime_choice_min_targets",
                    "_runtime_choice_max_targets",
                ):
                    flags.pop(key, None)
                return

            candidates = [
                uid for uid in player.deck
                if uid in engine.state.instances and _norm(engine.state.instances[uid].definition.card_type) == _norm("artefatto")
            ]
            if not candidates:
                engine.rng.shuffle(player.deck)
                return

            flags["_runtime_choice_source"] = expected_choice_source
            flags["_runtime_choice_candidates"] = ";;".join(candidates)
            flags["_runtime_choice_owner"] = str(target)
            flags["_runtime_choice_title"] = "Pietra Focaia"
            flags["_runtime_choice_prompt"] = "Scegli un Artefatto dal reliquiario da aggiungere alla mano."
            flags["_runtime_choice_min_targets"] = "1"
            flags["_runtime_choice_max_targets"] = "1"
            flags["_runtime_choice_ready"] = False
            flags["_runtime_reveal_card"] = source_uid
            flags["_runtime_waiting_for_reveal"] = True
            flags["_runtime_resume_source"] = source_uid
            flags["_runtime_resume_owner"] = str(owner_idx)
            flags["_runtime_pending_mode"] = "trigger_action"
            flags["_runtime_trigger_action"] = "choose_artifact_from_relicario_then_shuffle"
            flags["_runtime_trigger_target_player"] = str(effect.target_player or "me")
            return
        if action in {"optional_recover_all_matching_then_shuffle", "optional_recover_matching_then_shuffle"}:
            flags = engine.state.flags
            target = self._resolve_player_scope(owner_idx, effect.target_player or "me")
            player = engine.state.players[target]
            needle = _norm(effect.card_name or "")
            from_zone = _norm(effect.from_zone or effect.zone or "graveyard")
            to_zone = str(effect.to_zone or "relicario").strip() or "relicario"
            source_to_zone_on_yes = str(effect.to_zone_if or "").strip()
            should_shuffle = bool(effect.shuffle_after)
            max_to_move = int(effect.amount or 0)

            if from_zone == "graveyard":
                source_pool = list(player.graveyard)
            elif from_zone in {"deck", "relicario"}:
                source_pool = list(player.deck)
            elif from_zone == "excommunicated":
                source_pool = list(player.excommunicated)
            elif from_zone == "hand":
                source_pool = list(player.hand)
            else:
                source_pool = []

            candidates = [
                uid for uid in source_pool
                if uid in engine.state.instances
                and (not needle or needle in _norm(engine.state.instances[uid].definition.name))
            ]
            if max_to_move > 0:
                candidates = candidates[:max_to_move]
            candidate_names = [engine.state.instances[uid].definition.name for uid in candidates]
            listed = ", ".join(candidate_names) if candidate_names else "Nessuna carta."

            choice_source = str(flags.get("_runtime_choice_source", "")).strip()
            choice_ready = bool(flags.get("_runtime_choice_ready"))
            expected_choice_source = (
                f"{source_uid}:optional_recover_matching_then_shuffle:{target}:{from_zone}:{to_zone}:{needle}:{max_to_move}"
            )

            if choice_ready and choice_source == expected_choice_source:
                selected = str(flags.get("_runtime_choice_selected", "")).strip().lower()
                for key in (
                    "_runtime_choice_source",
                    "_runtime_choice_ready",
                    "_runtime_choice_selected",
                    "_runtime_choice_values",
                    "_runtime_choice_labels",
                    "_runtime_choice_owner",
                    "_runtime_choice_title",
                    "_runtime_choice_prompt",
                    "_runtime_choice_min_targets",
                    "_runtime_choice_max_targets",
                ):
                    flags.pop(key, None)

                if selected != "yes":
                    return

                moved = 0
                for uid in candidates:
                    if self._move_uid_to_zone(engine, uid, to_zone, target):
                        moved += 1
                if should_shuffle:
                    engine.rng.shuffle(player.deck)
                if moved > 0 and source_to_zone_on_yes:
                    source_inst = engine.state.instances.get(source_uid)
                    if source_inst is not None:
                        self._move_uid_to_zone(engine, source_uid, source_to_zone_on_yes, source_inst.owner)
                engine.state.log(f"Effetto opzionale risolto: {moved} carte spostate in {to_zone}.")
                return

            labels = {"yes": "Si, attiva", "no": "No, non attivare"}
            flags["_runtime_choice_source"] = expected_choice_source
            flags["_runtime_choice_values"] = "yes;;no"
            flags["_runtime_choice_labels"] = json.dumps(labels, ensure_ascii=False)
            flags["_runtime_choice_owner"] = str(target)
            flags["_runtime_choice_title"] = "Albero di Pietra"
            flags["_runtime_choice_prompt"] = (
                "Attivare l'effetto di Albero di Pietra?\n\n"
                f"Carte che verranno spostate da {from_zone} a {to_zone}: {listed}"
            )
            flags["_runtime_choice_min_targets"] = "1"
            flags["_runtime_choice_max_targets"] = "1"
            flags["_runtime_choice_ready"] = False
            flags["_runtime_reveal_card"] = source_uid
            flags["_runtime_waiting_for_reveal"] = True
            flags["_runtime_resume_source"] = source_uid
            flags["_runtime_resume_owner"] = str(owner_idx)
            flags["_runtime_pending_mode"] = "trigger_action"
            flags["_runtime_trigger_action"] = "optional_recover_matching_then_shuffle"
            flags["_runtime_trigger_target_player"] = str(effect.target_player or "me")
            flags["_runtime_trigger_card_name"] = str(effect.card_name or "")
            return
        if action == "summon_card_from_hand":
            selected = str(engine.state.flags.get("_runtime_selected_target", "")).strip()
            player = engine.state.players[owner_idx]
            selected_uid = selected if selected in engine.state.instances else None
            chosen_uid = selected_uid if selected_uid in player.hand else None
            if chosen_uid is None:
                card_name = _norm(effect.card_name or selected)
                if not card_name:
                    return
                for h_uid in list(player.hand):
                    if _norm(engine.state.instances[h_uid].definition.name) == card_name:
                        chosen_uid = h_uid
                        break
            if chosen_uid is None:
                return
            chosen_inst = engine.state.instances.get(chosen_uid)
            if chosen_inst is None:
                return
            board_owner = owner_idx
            if _norm(chosen_inst.definition.card_type) == _norm("santo") and self._has_invert_saint_summon_aura(engine):
                board_owner = 1 - board_owner
            board_player = engine.state.players[board_owner]
            slot = engine._first_open(board_player.attack)
            zone = "attack"
            if slot is None:
                slot = engine._first_open(board_player.defense)
                zone = "defense"
            if slot is None:
                return
            player.hand.remove(chosen_uid)
            if not engine.place_card_from_uid(board_owner, chosen_uid, zone, slot):
                player.hand.append(chosen_uid)
                return
            engine.state.flags.setdefault("activated_turn", {}).pop(chosen_uid, None)
            inst = engine.state.instances[chosen_uid]
            inst.exhausted = False
            engine.state.log(f"{player.name} evoca {inst.definition.name} dalla mano.")
            engine._emit_event("on_enter_field", owner_idx, card=chosen_uid, from_zone="hand")
            engine._emit_event("on_summoned_from_hand", owner_idx, card=chosen_uid)
            ctype = _norm(inst.definition.card_type)
            if ctype == _norm("token"):
                engine._emit_event("on_token_summoned", owner_idx, token=chosen_uid, summoner=owner_idx)
            elif ctype == _norm("santo"):
                engine._emit_event("on_opponent_saint_enters_field", 1 - owner_idx, saint=chosen_uid)
            enter_msg = self.resolve_enter(engine, owner_idx, chosen_uid)
            if enter_msg:
                engine.state.log(str(enter_msg))
            return
        if action == "summon_named_card":
            selected = str(engine.state.flags.get("_runtime_selected_target", "")).strip()
            selected_uid = selected if selected in engine.state.instances else None
            card_name = _norm(effect.card_name or selected)

            if not card_name and selected_uid is None:
                return

            player = engine.state.players[owner_idx]
            chosen_uid = None
            chosen_from_zone = None

            for pool_name in ("hand", "deck", "graveyard", "white_deck", "excommunicated"):
                pool = getattr(player, pool_name)
                for uid in list(pool):
                    if selected_uid is not None:
                        if uid != selected_uid:
                            continue
                    else:
                        if _norm(engine.state.instances[uid].definition.name) != card_name:
                            continue

                    chosen_uid = uid
                    chosen_from_zone = pool_name
                    pool.remove(uid)
                    break
                if chosen_uid:
                    break
            if chosen_uid is None:
                return
            chosen_inst = engine.state.instances[chosen_uid]
            chosen_type = _norm(chosen_inst.definition.card_type)
            board_owner = owner_idx
            board_player = player
            if chosen_type == "santo" and self._has_invert_saint_summon_aura(engine):
                board_owner = 1 - board_owner
                board_player = engine.state.players[board_owner]
            slot = None
            zone = ""
            if chosen_type in {"santo", "token"}:
                slot = engine._first_open(board_player.attack)
                zone = "attack"
                if slot is None:
                    slot = engine._first_open(board_player.defense)
                    zone = "defense"
            elif chosen_type == "artefatto":
                slot = engine._first_open(player.artifacts)
                zone = "artifact"
            elif chosen_type == "edificio":
                if player.building is None:
                    slot = 0
                    zone = "building"
            else:
                slot = engine._first_open(player.attack)
                zone = "attack"
                if slot is None:
                    slot = engine._first_open(player.defense)
                    zone = "defense"
            if slot is None or not zone:
                return
            if not engine.place_card_from_uid(board_owner, chosen_uid, zone, slot):
                return
            engine.state.flags.setdefault("activated_turn", {}).pop(chosen_uid, None)
            inst = engine.state.instances[chosen_uid]
            inst.exhausted = False
            engine.state.log(f"{player.name} evoca {inst.definition.name}.")
            actual_from_zone = chosen_from_zone or "summon"
            engine._emit_event("on_enter_field", owner_idx, card=chosen_uid, from_zone=actual_from_zone)

            if actual_from_zone == "graveyard":
                engine._emit_event("on_summoned_from_graveyard", owner_idx, card=chosen_uid)
            elif actual_from_zone == "hand":
                engine._emit_event("on_summoned_from_hand", owner_idx, card=chosen_uid)
            ctype = _norm(inst.definition.card_type)
            if ctype == _norm("token"):
                engine._emit_event("on_token_summoned", owner_idx, token=chosen_uid, summoner=owner_idx)
            elif ctype == _norm("santo"):
                engine._emit_event("on_opponent_saint_enters_field", 1 - owner_idx, saint=chosen_uid)
            enter_msg = self.resolve_enter(engine, owner_idx, chosen_uid)
            if enter_msg:
                engine.state.log(str(enter_msg))
            return
        if action == "summon_named_card_from_flag":
            flag_name = str(effect.flag or "").strip()
            if not flag_name:
                return
            raw_value = engine.state.flags.get(flag_name, 0)
            try:
                copies = int(raw_value)
            except (TypeError, ValueError):
                copies = 0
            if copies <= 0:
                engine.state.flags.pop(flag_name, None)
                return

            card_name = _norm(effect.card_name or "")
            if not card_name:
                engine.state.flags.pop(flag_name, None)
                return

            player = engine.state.players[owner_idx]
            for _ in range(copies):
                chosen_uid = None
                chosen_from_zone = None
                for pool_name in ("hand", "deck"):
                    pool = getattr(player, pool_name)
                    for uid in list(pool):
                        if _norm(engine.state.instances[uid].definition.name) != card_name:
                            continue
                        chosen_uid = uid
                        chosen_from_zone = pool_name
                        pool.remove(uid)
                        break
                    if chosen_uid:
                        break
                if chosen_uid is None:
                    break

                chosen_inst = engine.state.instances[chosen_uid]
                chosen_type = _norm(chosen_inst.definition.card_type)
                board_owner = owner_idx
                board_player = player
                if chosen_type == "santo" and self._has_invert_saint_summon_aura(engine):
                    board_owner = 1 - board_owner
                    board_player = engine.state.players[board_owner]
                slot = None
                zone = ""
                if chosen_type in {"santo", "token"}:
                    slot = engine._first_open(board_player.attack)
                    zone = "attack"
                    if slot is None:
                        slot = engine._first_open(board_player.defense)
                        zone = "defense"
                elif chosen_type == "artefatto":
                    slot = engine._first_open(player.artifacts)
                    zone = "artifact"
                elif chosen_type == "edificio":
                    if player.building is None:
                        slot = 0
                        zone = "building"
                else:
                    slot = engine._first_open(player.attack)
                    zone = "attack"
                    if slot is None:
                        slot = engine._first_open(player.defense)
                        zone = "defense"
                if slot is None or not zone:
                    if chosen_from_zone:
                        getattr(player, chosen_from_zone).insert(0, chosen_uid)
                    break
                if not engine.place_card_from_uid(board_owner, chosen_uid, zone, slot):
                    if chosen_from_zone:
                        getattr(player, chosen_from_zone).insert(0, chosen_uid)
                    break

                engine.state.flags.setdefault("activated_turn", {}).pop(chosen_uid, None)
                inst = engine.state.instances[chosen_uid]
                inst.exhausted = False
                engine.state.log(f"{player.name} evoca {inst.definition.name}.")
                actual_from_zone = chosen_from_zone or "summon"
                engine._emit_event("on_enter_field", owner_idx, card=chosen_uid, from_zone=actual_from_zone)

                if actual_from_zone == "graveyard":
                    engine._emit_event("on_summoned_from_graveyard", owner_idx, card=chosen_uid)
                elif actual_from_zone == "hand":
                    engine._emit_event("on_summoned_from_hand", owner_idx, card=chosen_uid)
                ctype = _norm(inst.definition.card_type)
                if ctype == _norm("token"):
                    engine._emit_event("on_token_summoned", owner_idx, token=chosen_uid, summoner=owner_idx)
                elif ctype == _norm("santo"):
                    engine._emit_event("on_opponent_saint_enters_field", 1 - owner_idx, saint=chosen_uid)
                enter_msg = self.resolve_enter(engine, owner_idx, chosen_uid)
                if enter_msg:
                    engine.state.log(str(enter_msg))

            engine.state.flags.pop(flag_name, None)
            return
        
        if action == "summon_generated_token":
            token_name = str(effect.card_name or "").strip()
            if not token_name:
                return
            summon_owner = self._resolve_owner_scope(owner_idx, effect.owner or "me")
            copies = max(1, int(effect.amount or 1))
            preferred_zone = str(effect.zone or "").strip() or None
            for _ in range(copies):
                self._summon_generated_token(
                    engine,
                    summon_owner,
                    token_name,
                    preferred_zone=preferred_zone,
                )
            return
        if action == "summon_generated_token_in_each_free_saint_slot":
            token_name = str(effect.card_name or "").strip()
            if not token_name:
                return
            summon_owner = self._resolve_owner_scope(owner_idx, effect.owner or "me")
            player = engine.state.players[summon_owner]
            free_slots = sum(1 for uid in player.attack if uid is None) + sum(1 for uid in player.defense if uid is None)
            for _ in range(max(0, int(free_slots))):
                self._summon_generated_token(engine, summon_owner, token_name)
            return

        if action == "summon_token":
            token_name = str(effect.card_name or "").strip()
            if not token_name:
                engine.state.log("summon_token: card_name vuoto.")
                return

            source_inst = engine.state.instances.get(source_uid)
            source_name = source_inst.definition.name if source_inst is not None else source_uid

            per_turn_key = f"spirito_esercito_dorato_used:{owner_idx}:{source_uid}:{engine.state.turn_number}"
            if engine.state.flags.get(per_turn_key):
                engine.state.log(f"{source_name}: effetto già usato in questo turno.")
                return

            summoned_uid = self._summon_generated_token(engine, owner_idx, token_name)
            if summoned_uid is None:
                engine.state.log(f"{source_name}: evocazione del token fallita.")
                return

            engine.state.flags[per_turn_key] = True
            engine.state.log(f"{source_name}: token evocato con successo ({token_name}).")
            return

        if action == "move_to_deck_bottom":
            for t_uid in targets:
                inst = engine.state.instances.get(t_uid)
                if inst is None:
                    continue
                owner = inst.owner
                if engine.move_graveyard_card_to_deck_bottom(owner, t_uid):
                    engine.state.log(f"{inst.definition.name} torna nel reliquiario.")
            return
        if action == "move_to_relicario":
            for t_uid in targets:
                inst = engine.state.instances.get(t_uid)
                if inst is None:
                    continue
                owner = inst.owner
                if self._move_uid_to_zone(engine, t_uid, "deck_bottom", owner):
                    engine.state.log(f"{inst.definition.name} torna nel reliquiario.")
            return
        if action == "shuffle_deck":
            target = self._resolve_player_scope(owner_idx, effect.target_player or "me")
            engine.rng.shuffle(engine.state.players[target].deck)
            return
        if action == "shuffle_target_owner_decks":
            owners = {engine.state.instances[t_uid].owner for t_uid in targets if t_uid in engine.state.instances}
            for owner in owners:
                engine.rng.shuffle(engine.state.players[owner].deck)
            return
        if action == "move_source_to_board":
            source = str(engine.state.flags.get("_runtime_source_card", ""))
            if not source or source not in engine.state.instances:
                return
            player = engine.state.players[owner_idx]
            if source not in player.hand:
                return
            requested = str(engine.state.flags.get("_runtime_selected_target", "")).strip().lower()
            slot = None
            zone = ""
            if requested:
                parsed_zone, parsed_slot = engine._parse_zone_target(requested)
                if parsed_zone in {"attack", "defense"} and parsed_slot >= 0:
                    slots = player.attack if parsed_zone == "attack" else player.defense
                    if parsed_slot < len(slots) and slots[parsed_slot] is None:
                        zone = parsed_zone
                        slot = parsed_slot
            if slot is None:
                slot = engine._first_open(player.attack)
                zone = "attack"
                if slot is None:
                    slot = engine._first_open(player.defense)
                    zone = "defense"
                if slot is None:
                    return
            player.hand.remove(source)
            if not engine.place_card_from_uid(owner_idx, source, zone, slot):
                player.hand.append(source)
                return
            engine.state.flags.setdefault("activated_turn", {}).pop(source, None)
            inst = engine.state.instances[source]
            inst.exhausted = False
            engine.state.log(f"{player.name} posiziona {inst.definition.name}.")
            engine._emit_event("on_enter_field", owner_idx, card=source, from_zone="hand")
            engine._emit_event("on_summoned_from_hand", owner_idx, card=source)
            ctype = _norm(inst.definition.card_type)
            if ctype == _norm("token"):
                engine._emit_event("on_token_summoned", owner_idx, token=source, summoner=owner_idx)
            elif ctype == _norm("santo"):
                engine._emit_event("on_opponent_saint_enters_field", 1 - owner_idx, saint=source)
            enter_msg = self.resolve_enter(engine, owner_idx, source)
            if enter_msg:
                engine.state.log(str(enter_msg))
            return
        if action == "request_end_turn":
            runtime_state = engine.state.flags.setdefault("runtime_state", {})
            runtime_state["request_end_turn"] = True
            return
        if action == "set_next_turn_draw_override":
            target = self._resolve_player_scope(owner_idx, effect.target_player or "me")
            amount = max(0, int(effect.amount or 0))
            flags = engine.state.flags.setdefault("next_turn_draw_override", {"0": 0, "1": 0})
            flags[str(target)] = amount
            return
        if action == "set_double_cost_next_turn":
            target = self._resolve_player_scope(owner_idx, effect.target_player or "opponent")
            amount = max(0, int(effect.amount or 1))
            flags = engine.state.flags.setdefault("double_cost_next_turn", {"0": 0, "1": 0})
            key = str(target)
            flags[key] = int(flags.get(key, 0)) + amount
            return
        if action == "set_no_attacks_until_card_draw":
            runtime_state = engine.state.flags.setdefault("runtime_state", {})
            locked_sources = list(runtime_state.get("no_attacks_until_draw_sources", []) or [])
            if source_uid and source_uid not in locked_sources:
                locked_sources.append(source_uid)
            runtime_state["no_attacks_until_draw_sources"] = locked_sources
            return
        if action == "set_no_attacks_this_turn":
            engine.state.flags["no_attacks_turn"] = int(engine.state.turn_number)
            return
        if action == "swap_attack_defense_rows":
            target = self._resolve_player_scope(owner_idx, effect.target_player or "opponent")
            player = engine.state.players[target]
            player.attack, player.defense = player.defense, player.attack
            return
        if action == "transfer_target_control_until_turn_end":
            target_controller = self._resolve_player_scope(owner_idx, effect.target_player or "opponent")
            runtime_state = engine.state.flags.setdefault("runtime_state", {})
            pending_returns = list(runtime_state.get("temporary_control_returns", []) or [])
            expire_turn = int(engine.state.turn_number)

            for t_uid in targets:
                inst = engine.state.instances.get(t_uid)
                if inst is None:
                    continue
                if _norm(inst.definition.card_type) not in {"santo", "token"}:
                    continue

                board_owner = engine._find_board_owner_of_uid(t_uid)
                if board_owner is None or int(board_owner) == int(target_controller):
                    continue

                from_player = engine.state.players[board_owner]
                to_player = engine.state.players[target_controller]

                from_zone = ""
                from_slot = -1
                if t_uid in from_player.attack:
                    from_zone = "attack"
                    from_slot = int(from_player.attack.index(t_uid))
                    from_player.attack[from_slot] = None
                    back_uid = from_player.defense[from_slot]
                    if back_uid is not None and from_player.attack[from_slot] is None:
                        from_player.attack[from_slot] = back_uid
                        from_player.defense[from_slot] = None
                elif t_uid in from_player.defense:
                    from_zone = "defense"
                    from_slot = int(from_player.defense.index(t_uid))
                    from_player.defense[from_slot] = None
                else:
                    continue

                placed = False
                if from_zone == "attack" and 0 <= from_slot < len(to_player.attack) and to_player.attack[from_slot] is None:
                    to_player.attack[from_slot] = t_uid
                    placed = True
                elif from_zone == "defense" and 0 <= from_slot < len(to_player.defense) and to_player.defense[from_slot] is None:
                    to_player.defense[from_slot] = t_uid
                    placed = True
                else:
                    slot = engine._first_open(to_player.attack)
                    if slot is not None:
                        to_player.attack[slot] = t_uid
                        placed = True
                    else:
                        slot = engine._first_open(to_player.defense)
                        if slot is not None:
                            to_player.defense[slot] = t_uid
                            placed = True

                if not placed:
                    if from_zone == "attack" and 0 <= from_slot < len(from_player.attack) and from_player.attack[from_slot] is None:
                        from_player.attack[from_slot] = t_uid
                    elif from_zone == "defense" and 0 <= from_slot < len(from_player.defense) and from_player.defense[from_slot] is None:
                        from_player.defense[from_slot] = t_uid
                    else:
                        fallback_slot = engine._first_open(from_player.attack)
                        if fallback_slot is not None:
                            from_player.attack[fallback_slot] = t_uid
                        else:
                            fallback_slot = engine._first_open(from_player.defense)
                            if fallback_slot is not None:
                                from_player.defense[fallback_slot] = t_uid
                    continue

                if "sin_to_controller_on_death" not in inst.blessed:
                    inst.blessed.append("sin_to_controller_on_death")

                pending_returns = [rec for rec in pending_returns if str(rec.get("uid", "")) != t_uid]
                pending_returns.append(
                    {
                        "uid": t_uid,
                        "from_owner": int(board_owner),
                        "to_owner": int(target_controller),
                        "from_zone": from_zone,
                        "from_slot": int(from_slot),
                        "expires_turn": expire_turn,
                    }
                )

            runtime_state["temporary_control_returns"] = pending_returns
            return
        if action == "set_attack_shield_this_turn":
            target = self._resolve_player_scope(owner_idx, effect.target_player or "me")
            shield = engine.state.flags.setdefault("attack_shield_turn", {})
            shield[str(target)] = int(engine.state.turn_number)
            return
        if action == "set_attack_shield_next_opponent_turn":
            target = self._resolve_player_scope(owner_idx, effect.target_player or "me")
            shield = engine.state.flags.setdefault("attack_shield_turn", {})
            shield[str(target)] = int(engine.state.turn_number) + 1
            return
        if action == "win_the_game":
            winner = self._resolve_player_scope(owner_idx, effect.target_player or "me")
            if engine.state.winner is None:
                engine.state.winner = int(winner)
                engine.state.log(f"{engine.state.players[winner].name} vince il duello per effetto carta.")
            return
        if action == "swap_attack_defense":
            player = engine.state.players[owner_idx]
            attack_slot = next((i for i, uid in enumerate(player.attack) if uid is not None), None)
            defense_slot = next((i for i, uid in enumerate(player.defense) if uid is not None), None)
            if attack_slot is None or defense_slot is None:
                return
            player.attack[attack_slot], player.defense[defense_slot] = player.defense[defense_slot], player.attack[attack_slot]
            return
        if action == "swap_selected_attack_defense":
            selected = str(engine.state.flags.get("_runtime_selected_target", "")).strip()
            selected_uids = [uid.strip() for uid in selected.split(",") if uid.strip()]
            if len(selected_uids) < 2:
                return

            uid_a = selected_uids[0]
            uid_b = selected_uids[1]
            if uid_a not in engine.state.instances or uid_b not in engine.state.instances:
                return

            controller_a = int(engine.state.instances[uid_a].owner)
            controller_b = int(engine.state.instances[uid_b].owner)
            if controller_a != controller_b:
                return

            player = engine.state.players[controller_a]
            attack_slot_a = next((i for i, uid in enumerate(player.attack) if uid == uid_a), None)
            defense_slot_a = next((i for i, uid in enumerate(player.defense) if uid == uid_a), None)
            attack_slot_b = next((i for i, uid in enumerate(player.attack) if uid == uid_b), None)
            defense_slot_b = next((i for i, uid in enumerate(player.defense) if uid == uid_b), None)

            uid_in_attack: str | None = None
            uid_in_defense: str | None = None
            attack_slot: int | None = None
            defense_slot: int | None = None

            if attack_slot_a is not None and defense_slot_b is not None:
                uid_in_attack = uid_a
                uid_in_defense = uid_b
                attack_slot = attack_slot_a
                defense_slot = defense_slot_b
            elif attack_slot_b is not None and defense_slot_a is not None:
                uid_in_attack = uid_b
                uid_in_defense = uid_a
                attack_slot = attack_slot_b
                defense_slot = defense_slot_a

            if uid_in_attack is None or uid_in_defense is None or attack_slot is None or defense_slot is None:
                return

            player.attack[attack_slot] = uid_in_defense
            player.defense[defense_slot] = uid_in_attack
            return
        if action == "increase_faith_per_opponent_saints":
            target_bonus = max(0, int(effect.amount))
            count = len(engine.all_saints_on_field(1 - owner_idx))
            for t_uid in targets:
                inst = engine.state.instances[t_uid]
                inst.current_faith = (inst.current_faith or 0) + (count * target_bonus)
            return
        if action == "increase_faith_if_damaged":
            amount = max(0, int(effect.amount))
            for t_uid in targets:
                inst = engine.state.instances[t_uid]
                base_faith = inst.definition.faith or 0
                current_faith = inst.current_faith if inst.current_faith is not None else base_faith
                if current_faith < base_faith:
                    inst.current_faith = current_faith + amount
            return
        if action == "pay_inspiration":
            target = self._resolve_player_scope(owner_idx, effect.target_player or "me")
            player = engine.state.players[target]

            cost = max(0, int(effect.amount))
            temp = max(0, int(getattr(player, "temporary_inspiration", 0)))
            normal = max(0, int(player.inspiration))

            use_temp = min(temp, cost)
            temp -= use_temp
            cost -= use_temp

            if cost > 0:
                normal = max(0, normal - cost)

            player.temporary_inspiration = temp
            player.inspiration = normal
            return
        if action == "pay_inspiration_per_target":
            target = self._resolve_player_scope(owner_idx, effect.target_player or "me")
            player = engine.state.players[target]

            cost = max(0, int(effect.amount)) * max(0, int(len(targets)))
            temp = max(0, int(getattr(player, "temporary_inspiration", 0)))
            normal = max(0, int(player.inspiration))

            use_temp = min(temp, cost)
            temp -= use_temp
            cost -= use_temp

            if cost > 0:
                normal = max(0, normal - cost)

            player.temporary_inspiration = temp
            player.inspiration = normal
            return

    #endregion
    @staticmethod
    #region Utility methods for effects
    def _resolve_player_scope(owner_idx: int, scope: str | None) -> int:
        key = _norm(scope or "me")
        if key in {"me", "owner", "controller", "self"}:
            return owner_idx
        if key in {"opponent", "enemy", "other"}:
            return 1 - owner_idx
        if key in {"player0", "p0", "0"}:
            return 0
        if key in {"player1", "p1", "1"}:
            return 1
        return owner_idx

    # This method is not currently used but can be helpful for future effects that need to count specific cards on the field.
    def _count_named_cards_on_field(self, engine: GameEngine, card_name: str) -> int:
        key = _norm(card_name)
        total = 0
        for idx in (0, 1):
            p = engine.state.players[idx]
            for uid in p.attack + p.defense + p.artifacts:
                if uid and _norm(engine.state.instances[uid].definition.name) == key:
                    total += 1
            if p.building and _norm(engine.state.instances[p.building].definition.name) == key:
                total += 1
        return total

    # This method is not currently used but can be helpful for future effects that need to count specific cards in a player's hand.
    def _effect_usage_state(self, engine: GameEngine) -> dict[str, int]:
        return engine.state.flags.setdefault("effect_usage_per_turn", {})

    # This method generates a unique key for tracking the usage of an effect based on the engine state, owner index, source UID, and effect details. This allows the system to enforce usage limits on effects that can only be used a certain number of times per turn.
    def _effect_usage_key(self, engine: GameEngine, owner_idx: int, source_uid: str, effect: EffectSpec) -> str:
        group = _norm(effect.action or "effect")
        return f"{group}:{owner_idx}:{source_uid}:{engine.state.turn_number}"

    # This method determines the usage limit for an effect based on its specification. If the effect has a defined usage limit per turn, it returns that limit (ensuring it's at least 1). If there is no usage limit specified, it returns 0, indicating that the effect can be used unlimited times.
    def _effect_usage_limit(self, effect: EffectSpec) -> int:
        if effect.usage_limit_per_turn is not None:
            return max(1, int(effect.usage_limit_per_turn))
        return 0

    # This method checks how many times a specific effect has been used by a player in the current turn. It retrieves the usage count from the engine's state using a unique key generated for that effect. If the effect has not been used yet, it defaults to 0.
    def _effect_usage_used(self, engine: GameEngine, owner_idx: int, source_uid: str, effect: EffectSpec) -> int:
        return int(self._effect_usage_state(engine).get(self._effect_usage_key(engine, owner_idx, source_uid, effect), 0))

    # This method checks if a specific effect can be used by a player based on its usage limit. If the effect has a usage limit of 0 or less, it can be used unlimited times, so the method returns True. Otherwise, it compares the number of times the effect has already been used with the defined limit and returns True if the effect can still be used, or False if the limit has been reached.
    def _effect_usage_can_use(self, engine: GameEngine, owner_idx: int, source_uid: str, effect: EffectSpec) -> bool:
        limit = self._effect_usage_limit(effect)
        if limit <= 0:
            return True
        return self._effect_usage_used(engine, owner_idx, source_uid, effect) < limit

    # This method should be called whenever an effect is successfully used to increment the usage count for that effect in the engine's state. It first checks the usage limit for the effect, and if there is a limit, it generates the unique key for that effect and increments the count in the state. If there is no limit, it does nothing.
    def _effect_usage_consume(self, engine: GameEngine, owner_idx: int, source_uid: str, effect: EffectSpec) -> None:
        limit = self._effect_usage_limit(effect)
        if limit <= 0:
            return
        key = self._effect_usage_key(engine, owner_idx, source_uid, effect)
        usage = self._effect_usage_state(engine)
        usage[key] = int(usage.get(key, 0)) + 1

    # This method implements the logic for an effect that allows a player to return a card to their hand once per turn. It checks if the effect has already been used this turn by looking for a specific marker in the source instance's blessed list. If the effect has not been used, it iterates through the target UIDs, attempts to move each card back to its owner's hand, and if successful, adds the marker to prevent further use of the effect this turn. It also emits an event for each card that leaves the field and returns to the hand.
    def _apply_return_to_hand_once_per_turn(
        self,
        engine: GameEngine,
        owner_idx: int,
        source_uid: str,
        targets: list[str],
    ) -> None:
        source_inst = engine.state.instances.get(source_uid)
        marker = f"once_per_turn:return_to_hand_once_per_turn:{engine.state.turn_number}"
        if source_inst is not None and marker in source_inst.blessed:
            return
        for uid in targets:
            inst = engine.state.instances.get(uid)
            if inst is None:
                continue
            owner = inst.owner
            if not engine.move_board_card_to_hand(owner, uid):
                continue
            if source_inst is not None and marker not in source_inst.blessed:
                source_inst.blessed.append(marker)
            engine._emit_event("on_this_card_leaves_field", owner, card=uid, destination="hand")

    # This method checks if a given event context matches the specified conditions for an effect. It evaluates the conditions recursively, allowing for complex logical structures using "all_of", "any_of", and "not". If the conditions are met, it returns True; otherwise, it returns False.
    def _event_matches(self, ctx: "RuleEventContext", owner_idx: int, condition: dict[str, Any]) -> bool:
        if not condition:
            return True
        return self._eval_condition_node(ctx, owner_idx, condition)

    # This method evaluates a condition node, which can contain logical operators ("all_of", "any_of", "not") and leaf conditions. It processes the logical structure accordingly and ultimately evaluates the leaf conditions to determine if the overall condition is satisfied.
    def _eval_condition_node(self, ctx: "RuleEventContext", owner_idx: int, node: dict[str, Any]) -> bool:
        if not node:
            return True
        all_of = node.get("all_of")
        if isinstance(all_of, list):
            for sub in all_of:
                if isinstance(sub, dict) and not self._eval_condition_node(ctx, owner_idx, sub):
                    return False
        any_of = node.get("any_of")
        if isinstance(any_of, list) and any_of:
            ok = False
            for sub in any_of:
                if isinstance(sub, dict) and self._eval_condition_node(ctx, owner_idx, sub):
                    ok = True
                    break
            if not ok:
                return False
        not_of = node.get("not")
        if isinstance(not_of, dict) and self._eval_condition_node(ctx, owner_idx, not_of):
            return False
        return self._eval_condition_leaf(ctx, owner_idx, node)

    # This method evaluates a leaf condition by checking various properties of the event context against the specified criteria. It checks for conditions related to the event's payload, such as zones, card ownership, card types, turn scope, phase, source card status, and target card properties. If any of the conditions are not met, it returns False; if all conditions are satisfied, it returns True.
    def _eval_condition_leaf(self, ctx: "RuleEventContext", owner_idx: int, condition: dict[str, Any]) -> bool:
        payload = ctx.payload
        event_card_uid = str(payload.get("card", payload.get("saint", payload.get("token", ""))))

        from_zone_in = condition.get("payload_from_zone_in")
        if from_zone_in:
            from_zone = _norm(str(payload.get("from_zone", "")))
            allowed = {_norm(z) for z in from_zone_in}
            if from_zone not in allowed:
                return False

        to_zone_in = condition.get("payload_to_zone_in")
        if to_zone_in:
            to_zone = _norm(str(payload.get("to_zone", payload.get("destination", ""))))
            allowed_to = {_norm(z) for z in to_zone_in}
            if to_zone not in allowed_to:
                return False
        target_slot_is_set = condition.get("payload_target_slot_is_set")
        if target_slot_is_set is not None:
            has_target_slot = payload.get("target_slot") is not None
            if bool(target_slot_is_set) != has_target_slot:
                return False

        owner_rule = _norm(str(condition.get("event_card_owner", "")))
        if owner_rule:
            if not event_card_uid:
                return False
            inst = ctx.engine.state.instances.get(event_card_uid)
            if inst is None:
                return False
            expected_owner = owner_idx if owner_rule in {"me", "owner", "controller"} else (1 - owner_idx)
            if int(inst.owner) != int(expected_owner):
                return False
        owner_attack_count_gte = condition.get("event_card_owner_attack_count_gte")
        if owner_attack_count_gte is not None:
            if not event_card_uid:
                return False
            inst = ctx.engine.state.instances.get(event_card_uid)
            if inst is None:
                return False
            attack_count = ctx.engine.state.flags.setdefault("attack_count", {"0": 0, "1": 0})
            if int(attack_count.get(str(inst.owner), 0)) < int(owner_attack_count_gte):
                return False

        ctype_in = condition.get("event_card_type_in")
        if ctype_in:
            if not event_card_uid:
                return False
            inst = ctx.engine.state.instances.get(event_card_uid)
            if inst is None:
                return False
            allowed_types = {_norm(v) for v in ctype_in}
            if _norm(inst.definition.card_type) not in allowed_types:
                return False

        turn_scope = _norm(str(condition.get("turn_scope", "")))
        if turn_scope:
            if turn_scope in {"my", "owner", "controller"} and int(ctx.engine.state.active_player) != int(owner_idx):
                return False
            if turn_scope in {"opponent", "enemy"} and int(ctx.engine.state.active_player) == int(owner_idx):
                return False

        phase_is = _norm(str(condition.get("phase_is", "")))
        if phase_is:
            runtime_state = ctx.engine.state.flags.setdefault("runtime_state", {})
            current_phase = _norm(str(runtime_state.get("phase", "")))
            if phase_is != current_phase:
                return False

        if condition.get("source_on_field") is True:
            source_uid = str(payload.get("source", "")).strip()
            if not source_uid:
                source_uid = str(ctx.engine.state.flags.get("_runtime_source_card", "")).strip()
            if not source_uid or not self._is_uid_on_field(ctx.engine, source_uid):
                return False
        source_counter_gte = condition.get("source_counter_gte")
        if source_counter_gte is not None:
            source_uid = str(payload.get("source", "")).strip()
            if not source_uid:
                source_uid = str(ctx.engine.state.flags.get("_runtime_source_card", "")).strip()
            if not source_uid or source_uid not in ctx.engine.state.instances:
                return False
            source_inst = ctx.engine.state.instances[source_uid]
            counter = 0
            for tag in list(source_inst.blessed):
                if not isinstance(tag, str) or not tag.startswith("campana_counter:"):
                    continue
                try:
                    counter = int(tag.split(":", 1)[1])
                except ValueError:
                    counter = 0
                break
            if counter < int(source_counter_gte):
                return False

        target_uid = str(payload.get("card", ""))
        if target_uid and target_uid in ctx.engine.state.instances:
            target_inst = ctx.engine.state.instances[target_uid]
            current_faith = target_inst.current_faith if target_inst.current_faith is not None else (target_inst.definition.faith or 0)
        else:
            target_inst = None
            current_faith = None

        target_current_faith_gte = condition.get("target_current_faith_gte")
        if target_current_faith_gte is not None:
            if current_faith is None or current_faith < int(target_current_faith_gte):
                return False

        controller_has_name = condition.get("controller_has_saint_with_name")
        if controller_has_name:
            wanted = _norm(str(controller_has_name))
            if not any(
                _card_matches_name(ctx.engine.state.instances[uid].definition, wanted)
                for uid in ctx.engine.all_saints_on_field(owner_idx)
            ):
                return False
        artifact_name = condition.get("controller_has_artifact_with_name")
        if artifact_name:
            wanted = _norm(str(artifact_name))
            if not any(
                a_uid and _card_matches_name(ctx.engine.state.instances[a_uid].definition, wanted)
                for a_uid in ctx.engine.state.players[owner_idx].artifacts
            ):
                return False
        controller_has_cards = condition.get("controller_has_cards")
        if isinstance(controller_has_cards, dict):
            min_count = max(0, int(controller_has_cards.get("min_count", 1) or 1))
            if len(self._collect_cards_for_requirement(ctx.engine, owner_idx, controller_has_cards)) < min_count:
                return False
        sacrifice_name = condition.get("can_play_by_sacrificing_specific_card_from_field")
        if sacrifice_name:
            wanted = _norm(str(sacrifice_name))
            p = ctx.engine.state.players[owner_idx]
            found = False
            for zone_uid in p.attack + p.defense + p.artifacts:
                if zone_uid and _card_matches_name(ctx.engine.state.instances[zone_uid].definition, wanted):
                    found = True
                    break
            if not found and p.building:
                found = _card_matches_name(ctx.engine.state.instances[p.building].definition, wanted)
            if not found:
                return False
        can_play_by_sacrificing = condition.get("can_play_by_sacrificing")
        if isinstance(can_play_by_sacrificing, dict):
            count = max(1, int(can_play_by_sacrificing.get("count", 1) or 1))
            if len(self._collect_cards_for_requirement(ctx.engine, owner_idx, can_play_by_sacrificing)) < count:
                return False

        hand_name = condition.get("controller_has_card_in_hand_with_name")
        if hand_name:
            wanted = _norm(str(hand_name))
            if not any(
                _card_matches_name(ctx.engine.state.instances[uid].definition, wanted)
                for uid in ctx.engine.state.players[owner_idx].hand
            ):
                return False
        building_name = condition.get("controller_has_building_with_name")
        if building_name:
            wanted = _norm(str(building_name))
            b_uid = ctx.engine.state.players[owner_idx].building
            if b_uid is None or not _card_matches_name(ctx.engine.state.instances[b_uid].definition, wanted):
                return False
        building_match = condition.get("controller_has_building_matching")
        if isinstance(building_match, dict):
            b_uid = ctx.engine.state.players[owner_idx].building
            if b_uid is None:
                return False
            req: dict[str, Any] = {"owner": "me", "zone": "field"}
            if "card_filter" in building_match and isinstance(building_match.get("card_filter"), dict):
                req["card_filter"] = dict(building_match.get("card_filter") or {})
            else:
                req["card_filter"] = dict(building_match)
            matches = self._collect_cards_for_requirement(ctx.engine, owner_idx, req)
            if b_uid not in matches:
                return False
        event_name_is = condition.get("event_card_name_is")
        if event_name_is:
            if not event_card_uid:
                return False
            wanted = _norm(str(event_name_is))
            inst = ctx.engine.state.instances.get(event_card_uid)
            if inst is None or not _card_matches_name(inst.definition, wanted):
                return False
        event_name_contains = condition.get("event_card_name_contains")
        if event_name_contains:
            if not event_card_uid:
                return False
            wanted = _norm(str(event_name_contains))
            inst = ctx.engine.state.instances.get(event_card_uid)
            if inst is None:
                return False
            if wanted not in _card_name_haystack(inst.definition):
                return False
        target_is_damaged = condition.get("target_is_damaged")
        if target_is_damaged:
            if target_inst is None:
                return False
            if (current_faith or 0) >= (target_inst.definition.faith or 0):
                return False
        deck_name = condition.get("controller_has_card_in_deck_with_name")
        if deck_name:
            wanted = _norm(str(deck_name))
            if not any(
                _card_matches_name(ctx.engine.state.instances[uid].definition, wanted)
                for uid in ctx.engine.state.players[owner_idx].deck
            ):
                return False
        drawn_this_turn_gte = condition.get("controller_drawn_cards_this_turn_gte")
        if drawn_this_turn_gte is not None:
            drawn = ctx.engine.state.flags.get("cards_drawn_this_turn", {})
            if len(drawn.get(str(owner_idx), [])) < int(drawn_this_turn_gte):
                return False
        hand_size_lte = condition.get("controller_hand_size_lte")
        if hand_size_lte is not None:
            if len(ctx.engine.state.players[owner_idx].hand) > int(hand_size_lte):
                return False
        saints_to_graveyard_gte = condition.get("controller_saints_sent_to_graveyard_this_turn_gte")
        if saints_to_graveyard_gte is not None:
            counts = ctx.engine.state.flags.get("saints_sent_to_graveyard_this_turn", {"0": 0, "1": 0})
            if int(counts.get(str(owner_idx), 0)) < int(saints_to_graveyard_gte):
                return False
        altare_sigilli_gte = condition.get("controller_altare_sigilli_gte")
        if altare_sigilli_gte is not None:
            if ctx.engine._get_altare_sigilli(owner_idx) < int(altare_sigilli_gte):
                return False
        distinct_saints_gte = condition.get("controller_has_distinct_saints_gte")
        if distinct_saints_gte is not None:
            names = {
                _norm(ctx.engine.state.instances[uid].definition.name)
                for uid in ctx.engine.all_saints_on_field(owner_idx)
            }
            if len(names) < int(distinct_saints_gte):
                return False
        selected_option = _norm(str(ctx.engine.state.flags.get("_runtime_selected_option", "")))
        selected_option_in = condition.get("selected_option_in")
        if selected_option_in:
            allowed = {_norm(v) for v in selected_option_in}
            if selected_option not in allowed:
                return False

        selected_target = _norm(str(ctx.engine.state.flags.get("_runtime_selected_target", "")))
        selected_target_in = condition.get("selected_target_in")
        if selected_target_in:
            allowed = {_norm(v) for v in selected_target_in}
            if selected_target not in allowed:
                return False
        selected_target_startswith = condition.get("selected_target_startswith")
        if selected_target_startswith:
            prefix = _norm(str(selected_target_startswith))
            if not selected_target.startswith(prefix):
                return False
        stored_card_matches = condition.get("stored_card_matches")
        if stored_card_matches:
            store_name = str(stored_card_matches.get("stored", "")).strip()
            if not store_name:
                return False

            stored_uid = str(ctx.engine.state.flags.get(f"_runtime_store_{store_name}", "")).strip()
            if not stored_uid:
                return False

            inst = ctx.engine.state.instances.get(stored_uid)
            if inst is None:
                return False

            filt = stored_card_matches.get("card_filter", {}) or {}

            name_haystack = _card_name_haystack(inst.definition)
            name_contains = _norm(str(filt.get("name_contains", "")))
            if name_contains and name_contains not in name_haystack:
                return False

            name_not_contains = _norm(str(filt.get("name_not_contains", "")))
            if name_not_contains and name_not_contains in name_haystack:
                return False

            type_filter = {_norm(v) for v in list(filt.get("card_type_in", []) or [])}
            if type_filter and _norm(inst.definition.card_type) not in type_filter:
                return False

        opp = 1 - owner_idx
        my_saints_gte = condition.get("my_saints_gte")
        if my_saints_gte is not None and len(ctx.engine.all_saints_on_field(owner_idx)) < int(my_saints_gte):
            return False
        my_saints_lte = condition.get("my_saints_lte")
        if my_saints_lte is not None and len(ctx.engine.all_saints_on_field(owner_idx)) > int(my_saints_lte):
            return False
        my_saints_lt_opponent = condition.get("my_saints_lt_opponent")
        if my_saints_lt_opponent:
            if len(ctx.engine.all_saints_on_field(owner_idx)) >= len(ctx.engine.all_saints_on_field(opp)):
                return False
        opp_saints_gte = condition.get("opponent_saints_gte")
        if opp_saints_gte is not None and len(ctx.engine.all_saints_on_field(opp)) < int(opp_saints_gte):
            return False
        opp_saints_lte = condition.get("opponent_saints_lte")
        if opp_saints_lte is not None and len(ctx.engine.all_saints_on_field(opp)) > int(opp_saints_lte):
            return False

        my_player = ctx.engine.state.players[owner_idx]
        opp_player = ctx.engine.state.players[opp]

        my_total_inspiration = int(my_player.inspiration) + int(getattr(my_player, "temporary_inspiration", 0))
        opp_total_inspiration = int(opp_player.inspiration) + int(getattr(opp_player, "temporary_inspiration", 0))

        my_insp_gte = condition.get("my_inspiration_gte")
        if my_insp_gte is not None and my_total_inspiration < int(my_insp_gte):
            return False

        my_insp_lte = condition.get("my_inspiration_lte")
        if my_insp_lte is not None and my_total_inspiration > int(my_insp_lte):
            return False

        my_spent_insp_gte = condition.get("my_spent_inspiration_turn_gte")
        if my_spent_insp_gte is not None:
            spent = ctx.engine.state.flags.get("spent_inspiration_turn", {"0": 0, "1": 0})
            if int(spent.get(str(owner_idx), 0)) < int(my_spent_insp_gte):
                return False

        my_attack_count_lte = condition.get("my_attack_count_lte")
        if my_attack_count_lte is not None:
            attack_count = ctx.engine.state.flags.get("attack_count", {"0": 0, "1": 0})
            if int(attack_count.get(str(owner_idx), 0)) > int(my_attack_count_lte):
                return False

        opp_insp_gte = condition.get("opponent_inspiration_gte")
        if opp_insp_gte is not None and opp_total_inspiration < int(opp_insp_gte):
            return False
        my_sin_gte = condition.get("my_sin_gte")
        if my_sin_gte is not None and int(ctx.engine.state.players[owner_idx].sin) < int(my_sin_gte):
            return False
        my_sin_lte = condition.get("my_sin_lte")
        if my_sin_lte is not None and int(ctx.engine.state.players[owner_idx].sin) > int(my_sin_lte):
            return False
        opp_sin_gte = condition.get("opponent_sin_gte")
        if opp_sin_gte is not None and int(ctx.engine.state.players[opp].sin) < int(opp_sin_gte):
            return False
        opp_sin_lte = condition.get("opponent_sin_lte")
        if opp_sin_lte is not None and int(ctx.engine.state.players[opp].sin) > int(opp_sin_lte):
            return False

        reason_in = condition.get("payload_reason_in")
        if reason_in:
            reason = _norm(str(payload.get("reason", "")))
            allowed_reason = {_norm(v) for v in reason_in}
            if reason not in allowed_reason:
                return False
        return True

    # This method collects card UIDs that match the specified requirement criteria for a given player. It considers the zones to search, applies card filters, and returns a list of matching card UIDs. The method also handles special script-based filters for specific card types.
    def _collect_cards_for_requirement(self, engine: GameEngine, owner_idx: int, requirement: dict[str, Any]) -> list[str]:
        owner_key = str(requirement.get("owner", "me"))
        zones = list(requirement.get("zones", []) or [])
        if not zones:
            zones = [str(requirement.get("zone", "field"))]

        card_filter = dict(requirement.get("card_filter", {}) or {})
        script_is_pyramid = card_filter.pop("script_is_pyramid", None)
        script_is_altare_sigilli = card_filter.pop("script_is_altare_sigilli", None)
        raw_crosses_gte = card_filter.get("crosses_gte")
        raw_crosses_lte = card_filter.get("crosses_lte")
        raw_strength_gte = card_filter.get("strength_gte")
        raw_strength_lte = card_filter.get("strength_lte")
        crosses_gte: int | None = None
        crosses_lte: int | None = None
        strength_gte: int | None = None
        strength_lte: int | None = None
        if raw_crosses_gte is not None:
            crosses_gte = int(raw_crosses_gte)
        if raw_crosses_lte is not None:
            crosses_lte = int(raw_crosses_lte)
        if raw_strength_gte is not None:
            strength_gte = int(raw_strength_gte)
        if raw_strength_lte is not None:
            strength_lte = int(raw_strength_lte)
        target = TargetSpec(
            type="cards_controlled_by_owner",
            owner=owner_key,
            zone=str(zones[0]) if zones else "field",
            zones=[str(z) for z in zones],
            card_filter=CardFilterSpec(
                name_in=[str(v) for v in list(card_filter.get("name_in", []) or [])],
                name_equals=str(card_filter.get("name_equals")) if card_filter.get("name_equals") is not None else None,
                name_contains=str(card_filter.get("name_contains")) if card_filter.get("name_contains") is not None else None,
                name_not_contains=(
                    str(card_filter.get("name_not_contains")) if card_filter.get("name_not_contains") is not None else None
                ),
                card_type_in=[str(v) for v in list(card_filter.get("card_type_in", []) or [])],
                crosses_gte=crosses_gte,
                crosses_lte=crosses_lte,
                strength_gte=strength_gte,
                strength_lte=strength_lte,
            ),
        )

        pool: list[str] = []
        for scoped_owner in self._target_owner_indices(owner_idx, owner_key):
            for zone_name in target.zones if target.zones else [target.zone]:
                pool.extend(self._get_zone_cards(engine, scoped_owner, zone_name))
        deduped_pool = list(dict.fromkeys(pool))
        filtered = self._filter_target_pool(engine, owner_idx, target, deduped_pool)
        if script_is_pyramid is not None:
            wanted = bool(script_is_pyramid)
            filtered = [
                uid
                for uid in filtered
                if self.get_is_pyramid(engine.state.instances[uid].definition.name) is wanted
            ]
        if script_is_altare_sigilli is not None:
            wanted = bool(script_is_altare_sigilli)
            filtered = [
                uid
                for uid in filtered
                if self.get_is_altare_sigilli(engine.state.instances[uid].definition.name) is wanted
            ]
        return filtered

    # This method is responsible for resolving any pending temporary control returns at the end of a player's turn. It checks the engine's state for any records of cards that need to be returned to their original controllers, verifies if the conditions for return are met (such as the current turn and the presence of the card on the field), and then moves the card back to its original position if necessary. If the card cannot be returned to its original position, it attempts to place it in an open slot on the field. The method also ensures that any "sin_to_controller_on_death" blessings are removed from the card when it is returned.
    def resolve_end_turn_runtime_hooks(self, engine: GameEngine, current_player_idx: int) -> None:
        runtime_state = engine.state.flags.setdefault("runtime_state", {})
        pending_returns = list(runtime_state.get("temporary_control_returns", []) or [])
        if not pending_returns:
            return

        keep: list[dict[str, Any]] = []
        current_turn = int(engine.state.turn_number)

        for rec in pending_returns:
            uid = str(rec.get("uid", "")).strip()
            expires_turn = int(rec.get("expires_turn", -1))
            if not uid or expires_turn != current_turn:
                keep.append(rec)
                continue
            if uid not in engine.state.instances:
                continue

            from_owner = int(rec.get("from_owner", -1))
            to_owner = int(rec.get("to_owner", -1))
            from_zone = _norm(str(rec.get("from_zone", "attack")))
            from_slot = int(rec.get("from_slot", -1))
            if from_owner not in (0, 1) or to_owner not in (0, 1):
                continue

            inst = engine.state.instances[uid]
            board_owner = engine._find_board_owner_of_uid(uid)
            if board_owner is None:
                inst.blessed = [tag for tag in inst.blessed if str(tag) != "sin_to_controller_on_death"]
                continue

            if int(board_owner) != int(to_owner):
                inst.blessed = [tag for tag in inst.blessed if str(tag) != "sin_to_controller_on_death"]
                continue

            to_player = engine.state.players[to_owner]
            moved_from_attack = False
            moved_slot = -1
            if uid in to_player.attack:
                moved_slot = int(to_player.attack.index(uid))
                to_player.attack[moved_slot] = None
                moved_from_attack = True
                back_uid = to_player.defense[moved_slot]
                if back_uid is not None and to_player.attack[moved_slot] is None:
                    to_player.attack[moved_slot] = back_uid
                    to_player.defense[moved_slot] = None
            elif uid in to_player.defense:
                moved_slot = int(to_player.defense.index(uid))
                to_player.defense[moved_slot] = None
            else:
                inst.blessed = [tag for tag in inst.blessed if str(tag) != "sin_to_controller_on_death"]
                continue

            from_player = engine.state.players[from_owner]
            placed = False
            if from_zone == "attack" and 0 <= from_slot < len(from_player.attack) and from_player.attack[from_slot] is None:
                from_player.attack[from_slot] = uid
                placed = True
            elif from_zone == "defense" and 0 <= from_slot < len(from_player.defense) and from_player.defense[from_slot] is None:
                from_player.defense[from_slot] = uid
                placed = True
            else:
                slot = engine._first_open(from_player.attack)
                if slot is not None:
                    from_player.attack[slot] = uid
                    placed = True
                else:
                    slot = engine._first_open(from_player.defense)
                    if slot is not None:
                        from_player.defense[slot] = uid
                        placed = True

            if not placed:
                if moved_from_attack and 0 <= moved_slot < len(to_player.attack) and to_player.attack[moved_slot] is None:
                    to_player.attack[moved_slot] = uid
                elif (not moved_from_attack) and 0 <= moved_slot < len(to_player.defense) and to_player.defense[moved_slot] is None:
                    to_player.defense[moved_slot] = uid
                else:
                    slot = engine._first_open(to_player.attack)
                    if slot is not None:
                        to_player.attack[slot] = uid
                    else:
                        slot = engine._first_open(to_player.defense)
                        if slot is not None:
                            to_player.defense[slot] = uid
                keep.append(rec)
                continue

            inst.blessed = [tag for tag in inst.blessed if str(tag) != "sin_to_controller_on_death"]

        runtime_state["temporary_control_returns"] = keep

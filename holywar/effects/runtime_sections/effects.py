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


class RuntimeEffectsMixin:
    """Target resolution, zone moves and low-level effect execution helpers."""
    if TYPE_CHECKING:
        _temp_faith: dict[int, dict[str, list[tuple[str, int, str]]]]

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
                        pool.extend(p.deck)
                    elif zone == "graveyard":
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

                if selected in engine.state.instances:
                    pool.append(selected)
                else:
                    source_uid = str(engine.state.flags.get("_runtime_source_card", "")).strip()
                    owner_key = _norm(target.owner)
                    allow_any_owner = owner_key in {"any", "both", "all", "either"}
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

                    if not resolved and fallback_uid:
                        pool.append(fallback_uid)
                        resolved = True

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

        elif ttype == "selected_targets":
            raw_selected = self._selected_target_raw_for_current_action(engine)
            if raw_selected:
                parts = [part.strip() for part in raw_selected.split(",") if part.strip()]
                source_uid = str(engine.state.flags.get("_runtime_source_card", "")).strip()
                owner_key = _norm(target.owner)
                allow_any_owner = owner_key in {"any", "both", "all", "either"}

                for selected in parts:
                    if selected.startswith("buff:"):
                        selected = selected.split(":", 1)[1]

                    if selected in engine.state.instances:
                        pool.append(selected)
                        continue

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

                    if not resolved and fallback_uid:
                        pool.append(fallback_uid)
                        resolved = True

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

        out = self._filter_target_pool(engine, owner_idx, target, pool)
        if target.max_targets is not None and target.max_targets >= 0:
            return out[: int(target.max_targets)]
        return out

    def _resolve_owner_scope(self, owner_idx: int, owner_key: str | None) -> int:
        key = _norm(owner_key or "me")
        return owner_idx if key in {"me", "owner", "controller"} else 1 - owner_idx

    def _target_owner_indices(self, owner_idx: int, owner_key: str | None) -> list[int]:
        key = _norm(owner_key or "me")
        if key in {"opponent", "enemy", "other"}:
            return [1 - owner_idx]
        if key in {"any", "both", "all", "either"}:
            return [owner_idx, 1 - owner_idx]
        return [owner_idx]

    def _get_zone_cards(self, engine: GameEngine, owner_idx: int, zone_name: str) -> list[str]:
        player = engine.state.players[owner_idx]
        zone = _norm(zone_name)

        if zone in {"deck", "relicario"}:
            return list(player.deck)
        if zone == "hand":
            return list(player.hand)
        if zone == "graveyard":
            return list(player.graveyard)
        if zone == "excommunicated":
            return list(player.excommunicated)

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

    def _move_uid_to_zone(self, engine: GameEngine, uid: str, to_zone: str, owner_idx: int) -> bool:
        inst = engine.state.instances.get(uid)
        if inst is None:
            return False

        real_owner = inst.owner
        player = engine.state.players[real_owner]
        zone = _norm(to_zone)
        from_zone = engine._locate_uid_zone(real_owner, uid)
        leaving_field = from_zone in {"attack", "defense", "artifact", "building"}

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

        self._remove_uid_from_all_player_zones(engine, real_owner, uid)
        if leaving_field:
            engine._reset_card_runtime_state(uid)

        if zone in {"deck_bottom", "bottom_of_deck"}:
            if uid not in player.deck:
                player.deck.insert(0, uid)
            else:
                player.deck.insert(0, player.deck.pop(player.deck.index(uid)))
            return True

        if zone in {"deck", "relicario"}:
            if uid not in player.deck:
                player.deck.append(uid)
            return True

        if zone == "graveyard":
            if uid not in player.graveyard:
                player.graveyard.append(uid)
            return True

        if zone == "excommunicated":
            if uid not in player.excommunicated:
                player.excommunicated.append(uid)
            return True

        return False

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

        max_num = 0
        for uid in engine.state.instances:
            if uid.startswith("c"):
                try:
                    max_num = max(max_num, int(uid[1:]))
                except ValueError:
                    pass
        new_uid = f"c{max_num + 1:05d}"

        token_copy = CardDefinition.from_dict(token_def.to_dict())
        engine.state.instances[new_uid] = CardInstance(
            uid=new_uid,
            definition=token_copy,
            owner=owner_idx,
            current_faith=token_copy.faith,
        )

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
                player = engine.state.players[owner]
                ctype = _norm(inst.definition.card_type)

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
                    blocked = min(state.ARTIFACT_SLOTS - 1, engine._count_artifact(1 - owner, "Gggnag'ljep"))
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
                    slot = engine._first_open(player.attack)
                    zone = "attack"
                    if slot is None:
                        slot = engine._first_open(player.defense)
                        zone = "defense"
                    if slot is not None and engine.place_card_from_uid(owner, t_uid, zone, slot):
                        placed = True

                if not placed:
                    if t_uid not in player.deck:
                        player.deck.insert(0, t_uid)
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
                    continue

                # Caso: carta nel deck
                if t_uid in player.deck:
                    player.deck.remove(t_uid)
                    if t_uid not in player.graveyard:
                        player.graveyard.append(t_uid)

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
        if action == "store_target_count":
            flag_name = str(effect.flag or "").strip()
            if not flag_name:
                return
            engine.state.flags[flag_name] = int(len(targets))
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
            slot = engine._first_open(player.attack)
            zone = "attack"
            if slot is None:
                slot = engine._first_open(player.defense)
                zone = "defense"
            if slot is None:
                return
            player.hand.remove(chosen_uid)
            if not engine.place_card_from_uid(owner_idx, chosen_uid, zone, slot):
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
            slot = None
            zone = ""
            if chosen_type in {"santo", "token"}:
                slot = engine._first_open(player.attack)
                zone = "attack"
                if slot is None:
                    slot = engine._first_open(player.defense)
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
            if not engine.place_card_from_uid(owner_idx, chosen_uid, zone, slot):
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
                slot = None
                zone = ""
                if chosen_type in {"santo", "token"}:
                    slot = engine._first_open(player.attack)
                    zone = "attack"
                    if slot is None:
                        slot = engine._first_open(player.defense)
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
                if not engine.place_card_from_uid(owner_idx, chosen_uid, zone, slot):
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
                player = engine.state.players[owner]
                moved = False
                if t_uid in player.hand:
                    player.hand.remove(t_uid)
                    player.deck.insert(0, t_uid)
                    moved = True
                elif t_uid in player.graveyard:
                    player.graveyard.remove(t_uid)
                    player.deck.insert(0, t_uid)
                    moved = True
                elif t_uid in player.excommunicated:
                    player.excommunicated.remove(t_uid)
                    player.deck.insert(0, t_uid)
                    moved = True
                elif t_uid in player.attack:
                    idx = player.attack.index(t_uid)
                    player.attack[idx] = None
                    player.deck.insert(0, t_uid)
                    moved = True
                elif t_uid in player.defense:
                    idx = player.defense.index(t_uid)
                    player.defense[idx] = None
                    player.deck.insert(0, t_uid)
                    moved = True
                elif t_uid in player.artifacts:
                    idx = player.artifacts.index(t_uid)
                    player.artifacts[idx] = None
                    player.deck.insert(0, t_uid)
                    moved = True
                elif player.building == t_uid:
                    player.building = None
                    player.deck.insert(0, t_uid)
                    moved = True
                if moved:
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

    @staticmethod
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

    def _effect_usage_state(self, engine: GameEngine) -> dict[str, int]:
        return engine.state.flags.setdefault("effect_usage_per_turn", {})

    def _effect_usage_key(self, engine: GameEngine, owner_idx: int, source_uid: str, effect: EffectSpec) -> str:
        group = _norm(effect.action or "effect")
        return f"{group}:{owner_idx}:{source_uid}:{engine.state.turn_number}"

    def _effect_usage_limit(self, effect: EffectSpec) -> int:
        if effect.usage_limit_per_turn is not None:
            return max(1, int(effect.usage_limit_per_turn))
        return 0

    def _effect_usage_used(self, engine: GameEngine, owner_idx: int, source_uid: str, effect: EffectSpec) -> int:
        return int(self._effect_usage_state(engine).get(self._effect_usage_key(engine, owner_idx, source_uid, effect), 0))

    def _effect_usage_can_use(self, engine: GameEngine, owner_idx: int, source_uid: str, effect: EffectSpec) -> bool:
        limit = self._effect_usage_limit(effect)
        if limit <= 0:
            return True
        return self._effect_usage_used(engine, owner_idx, source_uid, effect) < limit

    def _effect_usage_consume(self, engine: GameEngine, owner_idx: int, source_uid: str, effect: EffectSpec) -> None:
        limit = self._effect_usage_limit(effect)
        if limit <= 0:
            return
        key = self._effect_usage_key(engine, owner_idx, source_uid, effect)
        usage = self._effect_usage_state(engine)
        usage[key] = int(usage.get(key, 0)) + 1

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

    def _event_matches(self, ctx: "RuleEventContext", owner_idx: int, condition: dict[str, Any]) -> bool:
        if not condition:
            return True
        return self._eval_condition_node(ctx, owner_idx, condition)

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
        event_name_is = condition.get("event_card_name_is")
        if event_name_is:
            if not event_card_uid:
                return False
            wanted = _norm(str(event_name_is))
            inst = ctx.engine.state.instances.get(event_card_uid)
            if inst is None or not _card_matches_name(inst.definition, wanted):
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

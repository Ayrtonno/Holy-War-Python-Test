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


class RuntimeRegistryMixin:
    if TYPE_CHECKING:
        # Methods from RuntimeEffectsMixin
        def _eval_condition_node(self, ctx: RuleEventContext, owner_idx: int, node: dict[str, Any]) -> bool: ...
        def _collect_cards_for_requirement(self, engine: GameEngine, owner_idx: int, requirement: dict[str, Any]) -> list[str]: ...
    """Script registry bootstrap, migration and static card property accessors."""

    def __init__(self) -> None:
        self._scripts: dict[str, CardScript] = {}
        self._bindings: dict[int, dict[str, list[tuple[str, Callable[[RuleEventContext], None]]]]] = {}
        self._subscribed_engines: set[int] = set()
        self._temp_faith: dict[int, dict[str, list[tuple[str, int, str]]]] = {}
        self._bootstrap_from_cards_json()
        self._bootstrap_from_script_files()

    def clear_for_tests(self) -> None:
        self._scripts.clear()
        self._bindings.clear()
        self._subscribed_engines.clear()
        self._temp_faith.clear()

    def _bootstrap_from_cards_json(self) -> None:
        # runtime_sections/* lives under holywar/effects/runtime_sections;
        # cards.json is in holywar/data.
        cards_path = Path(__file__).resolve().parents[2] / "data" / "cards.json"
        if not cards_path.exists():
            return
        try:
            rows = json.loads(cards_path.read_text(encoding="utf-8"))
        except Exception:
            return
        if not isinstance(rows, list):
            return
        for row in rows:
            if not isinstance(row, dict):
                continue
            name = str(row.get("name", "")).strip()
            if not name:
                continue
            key = _norm(name)
            if key not in self._scripts:
                self._scripts[key] = CardScript(name=name)

    def register_script(self, script: CardScript) -> None:
        self._scripts[_norm(script.name)] = script

    def is_activate_once_per_turn(self, card_name: str) -> bool:
        script = self._scripts.get(_norm(card_name))
        return bool(script and script.activate_once_per_turn)

    def register_script_from_dict(self, card_name: str, spec: dict[str, Any]) -> None:
        def _to_int_or_none(value: Any) -> int | None:
            if value is None:
                return None
            return int(value)

        def _parse_effect(raw: dict[str, Any]) -> EffectSpec:
            usage_limit_raw = raw.get("usage_limit_per_turn")
            min_targets_raw = raw.get("min_targets")
            max_targets_raw = raw.get("max_targets")
            return EffectSpec(
                action=str(raw.get("action", "")),
                amount=int(raw.get("amount", 0)),
                duration=str(raw.get("duration", "permanent")),
                amount_multiplier_card_name=str(raw.get("amount_multiplier_card_name"))
                if raw.get("amount_multiplier_card_name") is not None
                else None,
                usage_limit_per_turn=_to_int_or_none(usage_limit_raw),
                target_player=str(raw.get("target_player")) if raw.get("target_player") is not None else None,
                card_name=str(raw.get("card_name")) if raw.get("card_name") is not None else None,
                flag=raw.get("flag"),
                owner=str(raw.get("owner")) if raw.get("owner") is not None else None,
                from_zone=str(raw.get("from_zone")) if raw.get("from_zone") is not None else None,
                zone=str(raw.get("zone")) if raw.get("zone") is not None else None,
                position=str(raw.get("position")) if raw.get("position") is not None else None,
                store_as=str(raw.get("store_as")) if raw.get("store_as") is not None else None,
                stored=str(raw.get("stored")) if raw.get("stored") is not None else None,
                to_zone=str(raw.get("to_zone")) if raw.get("to_zone") is not None else None,
                min_targets=_to_int_or_none(min_targets_raw),
                max_targets=_to_int_or_none(max_targets_raw),
                controller_has_saint_with_name=(
                    str(raw.get("controller_has_saint_with_name"))
                    if raw.get("controller_has_saint_with_name") is not None
                    else None
                ),
                to_zone_if_controller_has_saint_with_name=(
                    str(raw.get("to_zone_if_controller_has_saint_with_name"))
                    if raw.get("to_zone_if_controller_has_saint_with_name") is not None
                    else None
                ),
                to_zone_if_condition=(
                    dict(raw.get("to_zone_if_condition", {}) or {})
                    if raw.get("to_zone_if_condition") is not None
                    else None
                ),
                to_zone_if=(str(raw.get("to_zone_if")) if raw.get("to_zone_if") is not None else None),
                shuffle_after=bool(raw.get("shuffle_after", False)),
                choice_title=str(raw.get("choice_title")) if raw.get("choice_title") is not None else None,
                choice_prompt=str(raw.get("choice_prompt")) if raw.get("choice_prompt") is not None else None,
                choice_options=[
                    dict(v) for v in list(raw.get("choice_options", []) or []) if isinstance(v, dict)
                ],
            )

        def _parse_target(raw: dict[str, Any]) -> TargetSpec:
            filt = raw.get("card_filter", {}) or {}
            crosses_gte_raw = filt.get("crosses_gte")
            crosses_lte_raw = filt.get("crosses_lte")
            strength_gte_raw = filt.get("strength_gte")
            strength_lte_raw = filt.get("strength_lte")
            top_n_raw = filt.get("top_n_from_zone")
            target_min_raw = raw.get("min_targets")
            target_max_raw = raw.get("max_targets")
            return TargetSpec(
                type=str(raw.get("type", "cards_controlled_by_owner")),
                card_filter=CardFilterSpec(
                    name_in=[str(v) for v in list(filt.get("name_in", []) or [])],
                    name_equals=filt.get("name_equals"),
                    name_contains=filt.get("name_contains"),
                    name_not_contains=filt.get("name_not_contains"),
                    card_type_in=list(filt.get("card_type_in", []) or []),
                    exclude_event_card=bool(filt.get("exclude_event_card", False)),
                    exclude_buildings_if_my_building_zone_occupied=bool(
                        filt.get("exclude_buildings_if_my_building_zone_occupied", False)
                    ),
                    crosses_gte=_to_int_or_none(crosses_gte_raw),
                    crosses_lte=_to_int_or_none(crosses_lte_raw),
                    strength_gte=_to_int_or_none(strength_gte_raw),
                    strength_lte=_to_int_or_none(strength_lte_raw),
                    drawn_this_turn_only=bool(filt.get("drawn_this_turn_only", False)),
                    top_n_from_zone=_to_int_or_none(top_n_raw),
                ),
                zone=str(raw.get("zone", "field")),
                zones=list(raw.get("zones", []) or []),
                owner=str(raw.get("owner", "me")),
                min_targets=_to_int_or_none(target_min_raw),
                max_targets=_to_int_or_none(target_max_raw),
                max_targets_from=(dict(raw["max_targets_from"]) if raw.get("max_targets_from") is not None else None),
            )

        trig_specs: list[TriggeredEffectSpec] = []
        for t in spec.get("triggered_effects", []):
            trigger_raw = dict(t.get("trigger", {}) or {})
            trigger_condition = dict(trigger_raw.get("condition", {}) or {})
            entry_condition = dict(t.get("condition", {}) or {})
            if trigger_condition and entry_condition:
                merged_condition: dict[str, Any] = {"all_of": [trigger_condition, entry_condition]}
            elif entry_condition:
                merged_condition = entry_condition
            else:
                merged_condition = trigger_condition

            trig = TriggerSpec(
                event=str(trigger_raw.get("event", "")),
                frequency=str(trigger_raw.get("frequency", "each_turn")),
                condition=merged_condition,
            )
            target = _parse_target(t.get("target", {}) or {})
            effect = _parse_effect(t.get("effect", {}) or {})
            trig_specs.append(TriggeredEffectSpec(trigger=trig, target=target, effect=effect))
        on_play_actions: list[ActionSpec] = []
        for a in spec.get("on_play_actions", []):
            target = _parse_target(a.get("target", {}) or {})
            effect = _parse_effect(a.get("effect", {}) or {})
            on_play_actions.append(ActionSpec(target=target, effect=effect, condition=dict(a.get("condition", {}) or {})))
        on_enter_actions: list[ActionSpec] = []
        for a in spec.get("on_enter_actions", []):
            target = _parse_target(a.get("target", {}) or {})
            effect = _parse_effect(a.get("effect", {}) or {})
            on_enter_actions.append(ActionSpec(target=target, effect=effect, condition=dict(a.get("condition", {}) or {})))
        on_activate_actions: list[ActionSpec] = []
        for a in spec.get("on_activate_actions", []):
            target = _parse_target(a.get("target", {}) or {})
            effect = _parse_effect(a.get("effect", {}) or {})
            on_activate_actions.append(
                ActionSpec(target=target, effect=effect, condition=dict(a.get("condition", {}) or {}))
            )
        self.register_script(
            CardScript(
                name=card_name,
                on_play_mode=str(spec.get("on_play_mode", "auto")),
                on_enter_mode=str(spec.get("on_enter_mode", "auto")),
                on_activate_mode=str(spec.get("on_activate_mode", "auto")),
                activate_once_per_turn=bool(spec.get("activate_once_per_turn", False)),
                play_owner=str(spec.get("play_owner", "me")),
                can_play_from_hand=bool(spec.get("can_play_from_hand", True)),
                play_targeting=str(spec.get("play_targeting", "auto")),
                activate_targeting=str(spec.get("activate_targeting", "auto")),
                attack_targeting=str(spec.get("attack_targeting", "auto")),
                can_attack=bool(spec.get("can_attack", True)),
                attack_requirements=dict(spec.get("attack_requirements", {}) or {}),
                attack_blocked_message=(
                    str(spec.get("attack_blocked_message"))
                    if spec.get("attack_blocked_message") is not None
                    else None
                ),
                can_attack_from_defense=bool(spec.get("can_attack_from_defense", False)),
                can_attack_multiple_targets_in_attack_per_turn=bool(
                    spec.get("can_attack_multiple_targets_in_attack_per_turn", False)
                ),
                blocks_enemy_attackers_with_crosses_lte=(
                    int(spec["blocks_enemy_attackers_with_crosses_lte"])
                    if spec.get("blocks_enemy_attackers_with_crosses_lte") is not None
                    else None
                ),
                prevent_incoming_damage_if_less_than=(
                    int(spec["prevent_incoming_damage_if_less_than"])
                    if spec.get("prevent_incoming_damage_if_less_than") is not None
                    else None
                ),
                prevent_incoming_damage_to_card_types=[
                    str(v) for v in list(spec.get("prevent_incoming_damage_to_card_types", []) or [])
                ],
                battle_survival_mode=str(spec.get("battle_survival_mode", "none")),
                battle_survival_names=list(spec.get("battle_survival_names", []) or []),
                battle_survival_token_name=(
                    str(spec.get("battle_survival_token_name")) if spec.get("battle_survival_token_name") is not None else None
                ),
                battle_survival_restore_faith=(
                    int(spec.get("battle_survival_restore_faith", 0))
                    if spec.get("battle_survival_restore_faith") is not None
                    else None
                ),
                battle_excommunicate_on_lethal=bool(spec.get("battle_excommunicate_on_lethal", False)),
                post_battle_forced_destroy=bool(spec.get("post_battle_forced_destroy", False)),
                turn_start_summon_token_name=(
                    str(spec.get("turn_start_summon_token_name")) if spec.get("turn_start_summon_token_name") is not None else None
                ),
                auto_play_on_draw=bool(spec.get("auto_play_on_draw", False)),
                end_turn_on_draw=bool(spec.get("end_turn_on_draw", False)),
                strength_bonus_rules=[dict(rule) for rule in spec.get("strength_bonus_rules", []) if isinstance(rule, dict)],
                sigilli_strength_bonus_threshold=(
                    int(spec["sigilli_strength_bonus_threshold"])
                    if spec.get("sigilli_strength_bonus_threshold") is not None
                    else None
                ),
                sigilli_strength_bonus_amount=(
                    int(spec["sigilli_strength_bonus_amount"])
                    if spec.get("sigilli_strength_bonus_amount") is not None
                    else None
                ),
                incoming_damage_from_enemy_saints_divisor=max(
                    1,
                    int(spec.get("incoming_damage_from_enemy_saints_divisor", 1) or 1),
                ),
                strength_gain_on_damage_to_enemy_saint=int(spec.get("strength_gain_on_damage_to_enemy_saint", 0) or 0),
                strength_gain_on_lethal_to_enemy_saint=int(spec.get("strength_gain_on_lethal_to_enemy_saint", 0) or 0),
                grants_strength_to_friendly_saints=int(spec.get("grants_strength_to_friendly_saints", 0) or 0),
                grants_strength_to_friendly_saints_except_names=[
                    str(v) for v in list(spec.get("grants_strength_to_friendly_saints_except_names", []) or [])
                ],
                modifies_enemy_saints_strength=int(spec.get("modifies_enemy_saints_strength", 0) or 0),
                prevent_effect_destruction_of_friendly_saints_from_source_card_types=[
                    str(v)
                    for v in list(
                        spec.get("prevent_effect_destruction_of_friendly_saints_from_source_card_types", []) or []
                    )
                ],
                retaliation_damage_to_enemy_attacker=int(spec.get("retaliation_damage_to_enemy_attacker", 0) or 0),
                retaliation_reduce_sin_on_kill=int(spec.get("retaliation_reduce_sin_on_kill", 0) or 0),
                retaliation_multiplier_for_friendly_building_name=(
                    str(spec.get("retaliation_multiplier_for_friendly_building_name"))
                    if spec.get("retaliation_multiplier_for_friendly_building_name") is not None
                    else None
                ),
                play_requirements=dict(spec.get("play_requirements", {}) or {}),
                play_cost_fixed=(int(spec["play_cost_fixed"]) if spec.get("play_cost_fixed") is not None else None),
                play_cost_reduction_if_controller_has_card_type_in_hand=[
                    str(v) for v in list(spec.get("play_cost_reduction_if_controller_has_card_type_in_hand", []) or [])
                ],
                play_cost_zero_if_controller_has_saint_with_name=(
                    str(spec.get("play_cost_zero_if_controller_has_saint_with_name"))
                    if spec.get("play_cost_zero_if_controller_has_saint_with_name") is not None
                    else None
                ),
                play_cost_zero_if_controller_has_no_saints=bool(
                    spec.get("play_cost_zero_if_controller_has_no_saints", False)
                ),
                halves_friendly_saint_play_cost=bool(spec.get("halves_friendly_saint_play_cost", False)),
                halve_friendly_saint_play_cost_excludes_self=bool(
                    spec.get("halve_friendly_saint_play_cost_excludes_self", True)
                ),
                doubles_enemy_play_cost=bool(spec.get("doubles_enemy_play_cost", False)),
                is_pyramid=bool(spec.get("is_pyramid", False)),
                pyramid_strength_bonus_threshold=(
                    int(spec["pyramid_strength_bonus_threshold"])
                    if spec.get("pyramid_strength_bonus_threshold") is not None
                    else None
                ),
                pyramid_strength_bonus_amount=(
                    int(spec["pyramid_strength_bonus_amount"])
                    if spec.get("pyramid_strength_bonus_amount") is not None
                    else None
                ),
                pyramid_summon_extra_base_faith_threshold=(
                    int(spec["pyramid_summon_extra_base_faith_threshold"])
                    if spec.get("pyramid_summon_extra_base_faith_threshold") is not None
                    else None
                ),
                pyramid_summon_extra_base_faith_multiplier=(
                    int(spec["pyramid_summon_extra_base_faith_multiplier"])
                    if spec.get("pyramid_summon_extra_base_faith_multiplier") is not None
                    else None
                ),
                pyramid_turn_draw_bonus_threshold=(
                    int(spec["pyramid_turn_draw_bonus_threshold"])
                    if spec.get("pyramid_turn_draw_bonus_threshold") is not None
                    else None
                ),
                pyramid_turn_draw_bonus_amount=(
                    int(spec["pyramid_turn_draw_bonus_amount"])
                    if spec.get("pyramid_turn_draw_bonus_amount") is not None
                    else None
                ),
                is_altare_sigilli=bool(spec.get("is_altare_sigilli", False)),
                seals_level_size=(int(spec["seals_level_size"]) if spec.get("seals_level_size") is not None else None),
                seals_faith_per_level=(
                    int(spec["seals_faith_per_level"]) if spec.get("seals_faith_per_level") is not None else None
                ),
                seals_strength_per_level=(
                    int(spec["seals_strength_per_level"]) if spec.get("seals_strength_per_level") is not None else None
                ),
                immune_to_actions=[str(v) for v in list(spec.get("immune_to_actions", []) or []) if str(v).strip()],
                triggered_effects=trig_specs,
                on_play_actions=on_play_actions,
                on_enter_actions=on_enter_actions,
                on_activate_actions=on_activate_actions,
                counted_bonuses=[dict(v) for v in list(spec.get("counted_bonuses", []) or []) if isinstance(v, dict)],
            )
        )

    def _bootstrap_from_script_files(self) -> None:
        for card_name, spec in iter_card_scripts():
            self.register_script_from_dict(card_name, spec)

    def ensure_all_cards_migrated(self, engine: GameEngine) -> None:
        if not self._scripts:
            self._bootstrap_from_cards_json()
        self._bootstrap_from_script_files()
        for inst in engine.state.instances.values():
            key = _norm(inst.definition.name)
            if key not in self._scripts:
                self._scripts[key] = CardScript(name=inst.definition.name)
        self._ensure_leave_subscription(engine)

    def _ensure_leave_subscription(self, engine: "GameEngine") -> None:
        """Track engine subscription to prevent duplicate bindings."""
        engine_id = id(engine)
        if engine_id in self._subscribed_engines:
            return
        self._subscribed_engines.add(engine_id)

    def is_migrated(self, card_name: str) -> bool:
        return _norm(card_name) in self._scripts

    def get_script(self, card_name: str) -> CardScript | None:
        return self._scripts.get(_norm(card_name))

    def get_play_targeting_mode(self, card_name: str) -> str:
        script = self.get_script(card_name)
        if script is None:
            return "auto"
        return str(script.play_targeting or "auto").strip().lower() or "auto"

    def get_play_owner(self, card_name: str) -> str:
        script = self.get_script(card_name)
        if script is None:
            return "me"
        return str(script.play_owner or "me").strip().lower() or "me"

    def get_play_cost_fixed(self, card_name: str) -> int | None:
        script = self.get_script(card_name)
        if script is None:
            return None
        return script.play_cost_fixed

    def get_play_cost_reduction_if_controller_has_card_type_in_hand(self, card_name: str) -> list[str]:
        script = self.get_script(card_name)
        if script is None:
            return []
        return [str(v) for v in script.play_cost_reduction_if_controller_has_card_type_in_hand if str(v).strip()]

    def get_play_cost_zero_if_controller_has_saint_with_name(self, card_name: str) -> str | None:
        script = self.get_script(card_name)
        if script is None:
            return None
        value = str(script.play_cost_zero_if_controller_has_saint_with_name or "").strip()
        return value or None

    def get_play_cost_zero_if_controller_has_no_saints(self, card_name: str) -> bool:
        script = self.get_script(card_name)
        if script is None:
            return False
        return bool(script.play_cost_zero_if_controller_has_no_saints)

    def get_halves_friendly_saint_play_cost(self, card_name: str) -> bool:
        script = self.get_script(card_name)
        if script is None:
            return False
        return bool(script.halves_friendly_saint_play_cost)

    def get_halve_friendly_saint_play_cost_excludes_self(self, card_name: str) -> bool:
        script = self.get_script(card_name)
        if script is None:
            return True
        return bool(script.halve_friendly_saint_play_cost_excludes_self)

    def get_doubles_enemy_play_cost(self, card_name: str) -> bool:
        script = self.get_script(card_name)
        if script is None:
            return False
        return bool(script.doubles_enemy_play_cost)

    def get_activate_targeting_mode(self, card_name: str) -> str:
        script = self.get_script(card_name)
        if script is None:
            return "auto"
        return str(script.activate_targeting or "auto").strip().lower() or "auto"

    def get_attack_targeting_mode(self, card_name: str) -> str:
        script = self.get_script(card_name)
        if script is None:
            return "auto"
        return str(script.attack_targeting or "auto").strip().lower() or "auto"

    def get_can_attack(self, card_name: str) -> bool:
        script = self.get_script(card_name)
        if script is None:
            return True
        return bool(script.can_attack)

    def can_attack_now(self, engine: GameEngine, player_idx: int, uid: str) -> tuple[bool, str | None]:
        inst = engine.state.instances.get(uid)
        if inst is None:
            return False, "Carta attaccante non valida."
        script = self.get_script(inst.definition.name)
        if script is None or not script.attack_requirements:
            return True, None
        ok = self._eval_condition_node(
            RuleEventContext(engine=engine, event="can_attack", player_idx=player_idx, payload={"card": uid}),
            player_idx,
            script.attack_requirements,
        )
        if ok:
            return True, None
        msg = (script.attack_blocked_message or "").strip() or f"{inst.definition.name} non puo attaccare."
        return False, msg

    def get_can_attack_from_defense(self, card_name: str) -> bool:
        script = self.get_script(card_name)
        if script is None:
            return False
        return bool(script.can_attack_from_defense)

    def get_can_attack_multiple_targets_in_attack_per_turn(self, card_name: str) -> bool:
        script = self.get_script(card_name)
        if script is None:
            return False
        return bool(script.can_attack_multiple_targets_in_attack_per_turn)

    def get_blocks_enemy_attackers_with_crosses_lte(self, card_name: str) -> int | None:
        script = self.get_script(card_name)
        if script is None:
            return None
        raw = script.blocks_enemy_attackers_with_crosses_lte
        if raw is None:
            return None
        try:
            return int(raw)
        except (TypeError, ValueError):
            return None

    def get_prevent_incoming_damage_if_less_than(self, card_name: str) -> int | None:
        script = self.get_script(card_name)
        if script is None:
            return None
        return script.prevent_incoming_damage_if_less_than

    def get_prevent_incoming_damage_to_card_types(self, card_name: str) -> list[str]:
        script = self.get_script(card_name)
        if script is None:
            return []
        return [str(v) for v in script.prevent_incoming_damage_to_card_types if str(v).strip()]

    def get_battle_survival_mode(self, card_name: str) -> str:
        script = self.get_script(card_name)
        if script is None:
            return "none"
        return str(script.battle_survival_mode or "none").strip().lower() or "none"

    def get_battle_survival_names(self, card_name: str) -> list[str]:
        script = self.get_script(card_name)
        if script is None:
            return []
        return [str(name) for name in script.battle_survival_names if str(name).strip()]

    def get_battle_survival_token_name(self, card_name: str) -> str | None:
        script = self.get_script(card_name)
        if script is None:
            return None
        value = str(script.battle_survival_token_name or "").strip()
        return value or None

    def get_battle_survival_restore_faith(self, card_name: str) -> int | None:
        script = self.get_script(card_name)
        if script is None:
            return None
        return script.battle_survival_restore_faith

    def get_battle_excommunicate_on_lethal(self, card_name: str) -> bool:
        script = self.get_script(card_name)
        if script is None:
            return False
        return bool(script.battle_excommunicate_on_lethal)

    def get_post_battle_forced_destroy(self, card_name: str) -> bool:
        script = self.get_script(card_name)
        if script is None:
            return False
        return bool(script.post_battle_forced_destroy)

    def get_turn_start_summon_token_name(self, card_name: str) -> str | None:
        script = self.get_script(card_name)
        if script is None:
            return None
        value = str(script.turn_start_summon_token_name or "").strip()
        return value or None

    def get_auto_play_on_draw(self, card_name: str) -> bool:
        script = self.get_script(card_name)
        if script is None:
            return False
        return bool(script.auto_play_on_draw)

    def get_end_turn_on_draw(self, card_name: str) -> bool:
        script = self.get_script(card_name)
        if script is None:
            return False
        return bool(script.end_turn_on_draw)

    def get_strength_bonus_rules(self, card_name: str) -> list[dict[str, Any]]:
        script = self.get_script(card_name)
        if script is None:
            return []
        return [dict(rule) for rule in script.strength_bonus_rules]

    def get_faith_bonus_rules(self, card_name: str) -> list[dict]:
        script = self.get_script(card_name)
        if script is None:
            return []
        raw = getattr(script, "faith_bonus_rules", None)
        if isinstance(raw, list):
            return [dict(item) for item in raw if isinstance(item, dict)]
        return []

    def refresh_conditional_faith_bonuses(self, engine: "GameEngine", owner_idx: int) -> None:
        player = engine.state.players[owner_idx]
        field_uids = [uid for uid in (player.attack + player.defense) if uid]

        for uid in field_uids:
            inst = engine.state.instances[uid]
            base_faith = inst.definition.faith if inst.definition.faith is not None else 0

            old_bonus = 0
            kept_tags: list[str] = []
            for tag in inst.blessed:
                if isinstance(tag, str) and tag.startswith("conditional_faith_bonus:"):
                    try:
                        old_bonus += int(tag.split(":", 1)[1])
                    except ValueError:
                        pass
                else:
                    kept_tags.append(tag)
            inst.blessed = kept_tags

            new_bonus = 0
            for rule in self.get_faith_bonus_rules(inst.definition.name):
                required_name = str(rule.get("controller_has_card_with_name", "")).strip()
                required_zone = str(rule.get("controller_has_card_zone", "field")).strip().lower() or "field"
                required_self_name = str(rule.get("if_card_name", "")).strip()

                if required_self_name and _norm(inst.definition.name) != _norm(required_self_name):
                    continue

                in_zone = False
                if required_name:
                    if required_zone == "field":
                        in_zone = any(
                            _norm(engine.state.instances[f_uid].definition.name) == _norm(required_name)
                            for f_uid in field_uids
                        )
                    elif required_zone == "hand":
                        in_zone = any(
                            _norm(engine.state.instances[h_uid].definition.name) == _norm(required_name)
                            for h_uid in player.hand
                        )
                    elif required_zone in {"deck", "relicario"}:
                        in_zone = any(
                            _norm(engine.state.instances[d_uid].definition.name) == _norm(required_name)
                            for d_uid in player.deck
                        )
                    elif required_zone == "graveyard":
                        in_zone = any(
                            _norm(engine.state.instances[g_uid].definition.name) == _norm(required_name)
                            for g_uid in player.graveyard
                        )
                    elif required_zone == "excommunicated":
                        in_zone = any(
                            _norm(engine.state.instances[e_uid].definition.name) == _norm(required_name)
                            for e_uid in player.excommunicated
                        )

                    if not in_zone:
                        continue

                new_bonus += int(rule.get("self_bonus", 0) or 0)

            current_faith = inst.current_faith if inst.current_faith is not None else base_faith
            delta = new_bonus - old_bonus
            if delta != 0:
                inst.current_faith = max(0, current_faith + delta)

            if new_bonus:
                inst.blessed.append(f"conditional_faith_bonus:{new_bonus}")

    def get_sigilli_strength_bonus_threshold(self, card_name: str) -> int | None:
        script = self.get_script(card_name)
        if script is None:
            return None
        return script.sigilli_strength_bonus_threshold

    def get_sigilli_strength_bonus_amount(self, card_name: str) -> int | None:
        script = self.get_script(card_name)
        if script is None:
            return None
        return script.sigilli_strength_bonus_amount

    def get_is_pyramid(self, card_name: str) -> bool:
        script = self.get_script(card_name)
        if script is None:
            return False
        return bool(script.is_pyramid)

    def get_pyramid_strength_bonus_threshold(self, card_name: str) -> int | None:
        script = self.get_script(card_name)
        if script is None:
            return None
        return script.pyramid_strength_bonus_threshold

    def get_pyramid_strength_bonus_amount(self, card_name: str) -> int | None:
        script = self.get_script(card_name)
        if script is None:
            return None
        return script.pyramid_strength_bonus_amount

    def get_pyramid_summon_extra_base_faith_threshold(self, card_name: str) -> int | None:
        script = self.get_script(card_name)
        if script is None:
            return None
        return script.pyramid_summon_extra_base_faith_threshold

    def get_pyramid_summon_extra_base_faith_multiplier(self, card_name: str) -> int | None:
        script = self.get_script(card_name)
        if script is None:
            return None
        return script.pyramid_summon_extra_base_faith_multiplier

    def get_pyramid_turn_draw_bonus_threshold(self, card_name: str) -> int | None:
        script = self.get_script(card_name)
        if script is None:
            return None
        return script.pyramid_turn_draw_bonus_threshold

    def get_pyramid_turn_draw_bonus_amount(self, card_name: str) -> int | None:
        script = self.get_script(card_name)
        if script is None:
            return None
        return script.pyramid_turn_draw_bonus_amount

    def get_is_altare_sigilli(self, card_name: str) -> bool:
        script = self.get_script(card_name)
        if script is None:
            return False
        return bool(script.is_altare_sigilli)

    def get_seals_level_size(self, card_name: str) -> int | None:
        script = self.get_script(card_name)
        if script is None:
            return None
        return script.seals_level_size

    def get_seals_faith_per_level(self, card_name: str) -> int | None:
        script = self.get_script(card_name)
        if script is None:
            return None
        return script.seals_faith_per_level

    def get_seals_strength_per_level(self, card_name: str) -> int | None:
        script = self.get_script(card_name)
        if script is None:
            return None
        return script.seals_strength_per_level

    def is_immune_to_action(self, card_name: str, action_name: str) -> bool:
        script = self.get_script(card_name)
        if script is None:
            return False
        wanted = _norm(action_name)
        return any(_norm(v) == wanted for v in script.immune_to_actions)

    def get_counted_bonuses(self, card_name: str, context: str | None = None) -> list[dict[str, Any]]:
        script = self.get_script(card_name)
        if script is None:
            return []
        items = [dict(v) for v in script.counted_bonuses if isinstance(v, dict)]
        if context is None:
            return items
        wanted = _norm(context)
        return [it for it in items if _norm(str(it.get("context", ""))) == wanted]

    def get_context_bonus_amount(
        self,
        engine: GameEngine,
        owner_idx: int,
        context: str,
        amount_mode: str = "flat",
    ) -> int:
        player = engine.state.players[owner_idx]
        field_uids = [uid for uid in player.attack + player.defense + player.artifacts if uid]
        if player.building:
            field_uids.append(player.building)

        grouped: dict[str, int] = {}
        for source_uid in field_uids:
            source_inst = engine.state.instances.get(source_uid)
            if source_inst is None:
                continue
            rules = self.get_counted_bonuses(source_inst.definition.name, context=context)
            for idx, rule in enumerate(rules):
                if _norm(str(rule.get("amount_mode", "flat"))) != _norm(amount_mode):
                    continue
                req = dict(rule.get("requirement", {}) or {})
                candidates = self._collect_cards_for_requirement(engine, owner_idx, req)
                threshold = max(0, int(rule.get("threshold", 1) or 1))
                if len(candidates) < threshold:
                    continue
                amount = int(rule.get("amount", 0) or 0)
                if amount == 0:
                    continue
                group = str(rule.get("group", "")).strip() or f"{source_uid}:{idx}"
                stacking = _norm(str(rule.get("stacking", "max")))
                if stacking == "sum":
                    grouped[group] = int(grouped.get(group, 0)) + amount
                else:
                    grouped[group] = max(int(grouped.get(group, 0)), amount)
        return int(sum(grouped.values()))

    def get_incoming_damage_from_enemy_saints_divisor(self, card_name: str) -> int:
        script = self.get_script(card_name)
        if script is None:
            return 1
        return max(1, int(script.incoming_damage_from_enemy_saints_divisor or 1))

    def get_strength_gain_on_damage_to_enemy_saint(self, card_name: str) -> int:
        script = self.get_script(card_name)
        if script is None:
            return 0
        return int(script.strength_gain_on_damage_to_enemy_saint or 0)

    def get_strength_gain_on_lethal_to_enemy_saint(self, card_name: str) -> int:
        script = self.get_script(card_name)
        if script is None:
            return 0
        return int(script.strength_gain_on_lethal_to_enemy_saint or 0)

    def get_grants_strength_to_friendly_saints(self, card_name: str) -> int:
        script = self.get_script(card_name)
        if script is None:
            return 0
        return int(script.grants_strength_to_friendly_saints or 0)

    def get_grants_strength_to_friendly_saints_except_names(self, card_name: str) -> list[str]:
        script = self.get_script(card_name)
        if script is None:
            return []
        return [str(v) for v in script.grants_strength_to_friendly_saints_except_names if str(v).strip()]

    def get_modifies_enemy_saints_strength(self, card_name: str) -> int:
        script = self.get_script(card_name)
        if script is None:
            return 0
        return int(script.modifies_enemy_saints_strength or 0)

    def get_prevent_effect_destruction_of_friendly_saints_from_source_card_types(self, card_name: str) -> list[str]:
        script = self.get_script(card_name)
        if script is None:
            return []
        return [
            str(v).strip().lower()
            for v in script.prevent_effect_destruction_of_friendly_saints_from_source_card_types
            if str(v).strip()
        ]

    def get_retaliation_damage_to_enemy_attacker(self, card_name: str) -> int:
        script = self.get_script(card_name)
        if script is None:
            return 0
        return int(script.retaliation_damage_to_enemy_attacker or 0)

    def get_retaliation_reduce_sin_on_kill(self, card_name: str) -> int:
        script = self.get_script(card_name)
        if script is None:
            return 0
        return int(script.retaliation_reduce_sin_on_kill or 0)

    def get_retaliation_multiplier_for_friendly_building_name(self, card_name: str) -> str | None:
        script = self.get_script(card_name)
        if script is None:
            return None
        value = str(script.retaliation_multiplier_for_friendly_building_name or "").strip()
        return value or None

    def migrated_count(self) -> int:
        return len(self._scripts)

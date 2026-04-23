from __future__ import annotations

import json
import unicodedata
from dataclasses import dataclass, field
from pathlib import Path
from typing import TYPE_CHECKING, Any, Callable

from holywar.core import state
from holywar.core.state import MAX_HAND
from holywar.effects.card_scripts_loader import iter_card_scripts
from holywar.scripting_api import RuleEventContext
from holywar.core.state import CardInstance
from holywar.data.importer import load_cards_json
from holywar.data.models import CardDefinition

if TYPE_CHECKING:
    from holywar.core.engine import GameEngine
    from holywar.scripting_api import RuleEventContext


SUPPORTED_CONDITION_KEYS = {
    "all_of",
    "any_of",
    "not",
    "payload_from_zone_in",
    "payload_to_zone_in",
    "payload_target_slot_is_set",
    "event_card_owner",
    "event_card_type_in",
    "turn_scope",
    "phase_is",
    "source_on_field",
    "my_saints_gte",
    "my_saints_lte",
    "my_saints_lt_opponent",
    "opponent_saints_gte",
    "opponent_saints_lte",
    "my_inspiration_gte",
    "my_inspiration_lte",
    "opponent_inspiration_gte",
    "my_sin_gte",
    "my_sin_lte",
    "opponent_sin_gte",
    "opponent_sin_lte",
    "payload_reason_in",
    "target_current_faith_gte",
    "controller_has_saint_with_name",
    "controller_has_artifact_with_name",
    "can_play_by_sacrificing_specific_card_from_field",
    "controller_has_cards",
    "can_play_by_sacrificing",
    "controller_has_card_in_hand_with_name",
    "controller_has_card_in_deck_with_name",
    "controller_has_building_with_name",
    "controller_altare_sigilli_gte",
    "controller_drawn_cards_this_turn_gte",
    "controller_has_distinct_saints_gte",
    "selected_option_in",
    "selected_target_in",
    "selected_target_startswith",
    "event_card_name_is",
    "target_is_damaged",
    "controller_hand_size_lte",
    "stored_card_matches",
    "controller_saints_sent_to_graveyard_this_turn_gte",
    "event_card_owner_attack_count_gte",
}

EFFECT_ACTION_ALIASES = {
    "add_faith": "increase_faith",
    "buff_faith": "increase_faith",
    "remove_faith": "decrease_faith",
    "damage_faith": "decrease_faith",
    "buff_strength": "increase_strength",
    "add_strength": "increase_strength",
    "remove_strength": "decrease_strength",
    "draw_extra_card": "draw_cards",
    "add_draw": "draw_cards",
    "deal_sin": "inflict_sin",
    "add_sin": "inflict_sin",
    "reduce_sin": "remove_sin",
    "gain_inspiration": "add_inspiration",
    "pay_inspiration": "pay_inspiration",
}

SUPPORTED_EFFECT_ACTIONS = {
    "increase_faith",
    "decrease_faith",
    "increase_strength",
    "calice_upkeep",
    "calice_endturn",
    "add_seal_counter",
    "remove_seal_counter",
    "campana_add_counter",
    "cataclisma_ciclico",
    "kah_ok_tick",
    "trombe_del_giudizio_tick",
    "av_drna_on_opponent_draw",
    "pay_sin_or_destroy_self",
    "mill_cards",
    "draw_cards",
    "inflict_sin",
    "inflict_sin_to_target_owners",
    "remove_sin",
    "add_inspiration",
    "pay_inspiration",
    "excommunicate_top_cards_from_relicario",
    "remove_from_board_no_sin",
    "summon_card_from_hand",
    "summon_named_card",
    "summon_named_card_from_flag",
    "move_source_to_board",
    "move_to_deck_bottom",
    "move_to_relicario",
    "request_end_turn",
    "set_next_turn_draw_override",
    "set_double_cost_next_turn",
    "shuffle_deck",
    "shuffle_target_owner_decks",
    "summon_generated_token",
    "return_to_hand_once_per_turn",
    "swap_attack_defense",
    "increase_faith_per_opponent_saints",
    "increase_faith_if_damaged",
    "add_temporary_inspiration",
    "store_target_strength",
    "add_temporary_inspiration_from_flag",
    "summon_target_to_field",
    "remove_sin_equal_to_target_strength",
    "store_top_card_of_zone",
    "reveal_selected_target",
    "reveal_stored_card",
    "move_stored_card_to_zone",
    "move_source_to_zone",
    "optional_draw_from_top_n_then_shuffle",
    "optional_recover_from_graveyard_then_shuffle",
    "optional_recover_cards",
    "store_target_count",
    "draw_cards_from_flag",
    "choose_targets",
    "choose_option",
    "inflict_sin_from_flag",
    "store_target_faith",
    "excommunicate_card_no_sin",
    "store_target_faith_and_excommunicate_no_sin",
    "move_first_to_hand",
    "absorb_target_stats_and_link",
    "destroy_source_if_linked_to_event_card",
    "choose_artifact_from_relicario_then_shuffle",
    "inflict_sin_from_source_paid_inspiration",
    "optional_recover_all_matching_then_shuffle",
    "optional_recover_matching_then_shuffle",
    "destroy_all_saints_except_selected",
    "retaliate_damage_to_event_source_if_enemy_saint",
    "grant_attack_barrier",
    "prevent_specific_card_from_attacking",
    "halve_strength_rounded_down",
    "equip_card",
    "unequip_card",
    "destroy_equipment",
}


def _norm(text: str) -> str:
    value = unicodedata.normalize("NFKD", text or "")
    value = "".join(ch for ch in value if not unicodedata.combining(ch))
    return value.strip().lower()


def _card_aliases(definition: CardDefinition) -> list[str]:
    raw_aliases = getattr(definition, "aliases", []) or []
    if isinstance(raw_aliases, str):
        return [part.strip() for part in raw_aliases.split(",") if part.strip()]
    return [str(alias).strip() for alias in raw_aliases if str(alias).strip()]


def _card_name_variants(definition: CardDefinition) -> set[str]:
    variants = {_norm(definition.name)}
    variants.update(_norm(alias) for alias in _card_aliases(definition))
    return {v for v in variants if v}


def _card_name_haystack(definition: CardDefinition) -> str:
    parts = [definition.name, *_card_aliases(definition)]
    return " ".join(_norm(part) for part in parts if str(part).strip())


def _card_matches_name(definition: CardDefinition, wanted: str) -> bool:
    wanted_norm = _norm(wanted)
    if not wanted_norm:
        return False
    return wanted_norm in _card_name_variants(definition)


@dataclass(slots=True)
class TriggerSpec:
    event: str
    frequency: str = "each_turn"
    condition: dict[str, Any] = field(default_factory=dict)


@dataclass(slots=True)
class CardFilterSpec:
    name_in: list[str] = field(default_factory=list)
    name_equals: str | None = None
    name_contains: str | None = None
    name_not_contains: str | None = None
    card_type_in: list[str] = field(default_factory=list)
    exclude_event_card: bool = False
    exclude_buildings_if_my_building_zone_occupied: bool = False
    crosses_gte: int | None = None
    crosses_lte: int | None = None
    strength_gte: int | None = None
    strength_lte: int | None = None
    drawn_this_turn_only: bool = False
    top_n_from_zone: int | None = None


@dataclass(slots=True)
class TargetSpec:
    type: str
    card_filter: CardFilterSpec = field(default_factory=CardFilterSpec)
    zone: str = "field"
    zones: list[str] = field(default_factory=list)
    owner: str = "me"
    min_targets: int | None = None
    max_targets: int | None = None
    max_targets_from: dict[str, Any] | None = None


@dataclass(slots=True)
class EffectSpec:
    action: str
    amount: int = 0
    duration: str = "permanent"
    amount_multiplier_card_name: str | None = None
    usage_limit_per_turn: int | None = None
    target_player: str | None = None
    card_name: str | None = None
    flag: str | None = None

    owner: str | None = None
    from_zone: str | None = None
    zone: str | None = None
    position: str | None = None
    store_as: str | None = None
    stored: str | None = None
    to_zone: str | None = None
    min_targets: int | None = None
    max_targets: int | None = None
    controller_has_saint_with_name: str | None = None
    to_zone_if_controller_has_saint_with_name: str | None = None
    to_zone_if_condition: dict[str, Any] | None = None
    to_zone_if: str | None = None
    shuffle_after: bool = False
    choice_title: str | None = None
    choice_prompt: str | None = None
    choice_options: list[dict[str, Any]] = field(default_factory=list)


@dataclass(slots=True)
class TriggeredEffectSpec:
    trigger: TriggerSpec
    target: TargetSpec
    effect: EffectSpec


@dataclass(slots=True)
class ActionSpec:
    target: TargetSpec
    effect: EffectSpec
    condition: dict[str, Any] = field(default_factory=dict)


@dataclass(slots=True)
class CardScript:
    name: str
    on_play_mode: str = "auto"
    on_enter_mode: str = "auto"
    on_activate_mode: str = "auto"
    activate_once_per_turn: bool = False
    play_owner: str = "me"
    can_play_from_hand: bool = True
    play_targeting: str = "auto"
    play_requirements: dict[str, Any] = field(default_factory=dict)
    play_cost_fixed: int | None = None
    play_cost_reduction_if_controller_has_card_type_in_hand: list[str] = field(default_factory=list)
    play_cost_zero_if_controller_has_saint_with_name: str | None = None
    play_cost_zero_if_controller_has_no_saints: bool = False
    halves_friendly_saint_play_cost: bool = False
    halve_friendly_saint_play_cost_excludes_self: bool = True
    doubles_enemy_play_cost: bool = False
    activate_targeting: str = "auto"
    attack_targeting: str = "auto"
    can_attack: bool = True
    attack_requirements: dict[str, Any] = field(default_factory=dict)
    attack_blocked_message: str | None = None
    can_attack_from_defense: bool = False
    can_attack_multiple_targets_in_attack_per_turn: bool = False
    blocks_enemy_attackers_with_crosses_lte: int | None = None
    prevent_incoming_damage_if_less_than: int | None = None
    prevent_incoming_damage_to_card_types: list[str] = field(default_factory=list)
    battle_survival_mode: str = "none"
    battle_survival_names: list[str] = field(default_factory=list)
    battle_survival_token_name: str | None = None
    battle_survival_restore_faith: int | None = None
    battle_excommunicate_on_lethal: bool = False
    post_battle_forced_destroy: bool = False
    turn_start_summon_token_name: str | None = None
    auto_play_on_draw: bool = False
    end_turn_on_draw: bool = False
    strength_bonus_rules: list[dict[str, Any]] = field(default_factory=list)
    sigilli_strength_bonus_threshold: int | None = None
    sigilli_strength_bonus_amount: int | None = None
    is_pyramid: bool = False
    pyramid_strength_bonus_threshold: int | None = None
    pyramid_strength_bonus_amount: int | None = None
    pyramid_summon_extra_base_faith_threshold: int | None = None
    pyramid_summon_extra_base_faith_multiplier: int | None = None
    pyramid_turn_draw_bonus_threshold: int | None = None
    pyramid_turn_draw_bonus_amount: int | None = None
    is_altare_sigilli: bool = False
    seals_level_size: int | None = None
    seals_faith_per_level: int | None = None
    seals_strength_per_level: int | None = None
    immune_to_actions: list[str] = field(default_factory=list)
    incoming_damage_from_enemy_saints_divisor: int = 1
    strength_gain_on_damage_to_enemy_saint: int = 0
    strength_gain_on_lethal_to_enemy_saint: int = 0
    grants_strength_to_friendly_saints: int = 0
    grants_strength_to_friendly_saints_except_names: list[str] = field(default_factory=list)
    modifies_enemy_saints_strength: int = 0
    prevent_effect_destruction_of_friendly_saints_from_source_card_types: list[str] = field(default_factory=list)
    retaliation_damage_to_enemy_attacker: int = 0
    retaliation_reduce_sin_on_kill: int = 0
    retaliation_multiplier_for_friendly_building_name: str | None = None
    triggered_effects: list[TriggeredEffectSpec] = field(default_factory=list)
    on_play_actions: list[ActionSpec] = field(default_factory=list)
    on_enter_actions: list[ActionSpec] = field(default_factory=list)
    on_activate_actions: list[ActionSpec] = field(default_factory=list)
    counted_bonuses: list[dict[str, Any]] = field(default_factory=list)


from holywar.effects.runtime_sections import RuntimeRegistryMixin, RuntimeResolutionMixin, RuntimeEffectsMixin


class RuntimeCardManager(RuntimeRegistryMixin, RuntimeResolutionMixin, RuntimeEffectsMixin):
    """Facade class: concrete behavior is composed via runtime mixins."""
    pass


runtime_cards = RuntimeCardManager()


__all__ = [
    "TriggerSpec",
    "CardFilterSpec",
    "TargetSpec",
    "EffectSpec",
    "TriggeredEffectSpec",
    "ActionSpec",
    "CardScript",
    "RuntimeCardManager",
    "runtime_cards",
]

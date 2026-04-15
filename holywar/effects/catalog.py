from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from holywar.effects.runtime import (
    EFFECT_ACTION_ALIASES,
    SUPPORTED_CONDITION_KEYS,
    SUPPORTED_EFFECT_ACTIONS,
    runtime_cards,
)
from holywar.scripting_api import DECLARED_FUNCTIONS, RuleEvents


CANONICAL_EVENTS: set[str] = set(RuleEvents.ALL) | {
    "on_card_sent_to_reliquiary",
    "on_card_returned_to_reliquiary",
    "on_card_shuffled_into_reliquiary",
    "on_player_searches_reliquiary",
    "on_player_shuffles_reliquiary",
    "on_player_returns_from_graveyard_to_reliquiary",
}

CANONICAL_FUNCTIONS: set[str] = set(DECLARED_FUNCTIONS)

CANONICAL_ACTIONS: set[str] = set(SUPPORTED_EFFECT_ACTIONS) | {
    "add_seal_counter",
    "remove_seal_counter",
    "add_generic_counter",
    "remove_generic_counter",
    "set_seal_counter",
    "set_faith_to",
    "reset_faith_to_initial",
    "double_faith",
    "decrease_strength",
    "set_strength",
    "half_strength_round_down",
    "set_inspiration",
    "destroy_card",
    "destroy_all_saints_on_field",
    "destroy_all_saints_except_targets",
    "destroy_all_artifacts_and_buildings_on_field",
    "excommunicate_card",
    "send_from_field_to_graveyard",
    "send_from_hand_to_graveyard",
    "send_from_relicario_to_graveyard",
    "summon_from_hand",
    "summon_from_relicario",
    "summon_from_graveyard",
    "summon_from_excommunicated",
    "summon_token",
    "summon_multiple_tokens",
    "special_summon_by_effect",
    "equip_card",
    "unequip_card",
    "negate_effect_activation",
    "negate_card_destruction",
    "win_the_game",
}

CANONICAL_CONDITIONS: set[str] = set(SUPPORTED_CONDITION_KEYS) | {
    "controller_has",
    "opponent_has",
    "field_has_saint_with_name",
    "field_has_token",
    "controller_has_altar_with_seal_count",
    "opponent_has_no_saints_in_defense",
    "opponent_has_exactly_n_saints",
    "my_building_zone_is_occupied",
    "i_control_less_saints_than_opponent",
    "target_has_croci",
    "target_has_faith",
    "target_has_strength",
    "target_is_damaged",
    "target_is_in_attack_position",
    "target_is_in_defense_position",
    "target_has_expansion",
    "my_remaining_inspiration",
    "opponent_sin",
    "both_players_sin_less_than",
    "both_players_sin_more_than",
    "this_turn_phase_is",
    "it_is_my_first_turn",
    "can_play_without_inspiration_cost_if",
    "can_play_only_if",
}

# Backlog target from planning list:
# 90 game state + 80 player state + 110 card state + 80 properties + 100 conditions + 110 events = 570
BACKLOG_TARGET_IDS: tuple[str, ...] = tuple(
    [f"GS{i:03d}" for i in range(1, 91)]
    + [f"PS{i:03d}" for i in range(1, 81)]
    + [f"CS{i:03d}" for i in range(1, 111)]
    + [f"CP{i:03d}" for i in range(1, 81)]
    + [f"CN{i:03d}" for i in range(1, 101)]
    + [f"EV{i:03d}" for i in range(1, 111)]
)


@dataclass(slots=True)
class CoverageSnapshot:
    target_total: int
    implemented_events: int
    implemented_functions: int
    implemented_conditions: int
    implemented_actions: int
    script_count: int

    @property
    def implemented_total(self) -> int:
        return (
            self.implemented_events
            + self.implemented_functions
            + self.implemented_conditions
            + self.implemented_actions
        )

    @property
    def target_ratio(self) -> float:
        if self.target_total <= 0:
            return 0.0
        return self.implemented_total / float(self.target_total)


def current_coverage_snapshot() -> CoverageSnapshot:
    return CoverageSnapshot(
        target_total=len(BACKLOG_TARGET_IDS),
        implemented_events=len(CANONICAL_EVENTS),
        implemented_functions=len(CANONICAL_FUNCTIONS),
        implemented_conditions=len(SUPPORTED_CONDITION_KEYS),
        implemented_actions=len(SUPPORTED_EFFECT_ACTIONS),
        script_count=len(runtime_cards._scripts),  # noqa: SLF001 - intentional for diagnostics
    )


def _walk_condition_keys(node: Any, out: set[str]) -> None:
    if isinstance(node, dict):
        for k, v in node.items():
            out.add(str(k))
            _walk_condition_keys(v, out)
    elif isinstance(node, list):
        for it in node:
            _walk_condition_keys(it, out)


def validate_registered_scripts() -> dict[str, list[str]]:
    unknown_events: set[str] = set()
    unknown_actions: set[str] = set()
    unknown_condition_keys: set[str] = set()

    for script in runtime_cards._scripts.values():  # noqa: SLF001 - intentional diagnostics
        for te in script.triggered_effects:
            ev = str(te.trigger.event)
            if ev and ev not in CANONICAL_EVENTS:
                unknown_events.add(ev)
            action = str(te.effect.action).strip().lower()
            if action:
                canonical = EFFECT_ACTION_ALIASES.get(action, action)
                if canonical not in CANONICAL_ACTIONS:
                    unknown_actions.add(action)
            keys: set[str] = set()
            _walk_condition_keys(te.trigger.condition, keys)
            for key in keys:
                if key not in CANONICAL_CONDITIONS:
                    unknown_condition_keys.add(key)

    return {
        "unknown_events": sorted(unknown_events),
        "unknown_actions": sorted(unknown_actions),
        "unknown_condition_keys": sorted(unknown_condition_keys),
    }


from __future__ import annotations

CARD_NAME = """Camazotz"""

SCRIPT = {
    "default_selection_mode": "prompt",
    "default_cancel_behavior": "abort_step",
    "default_target_policy": "optional_resolve",
    "default_placement_policy": "prompt_slot_required",
    "default_activation_mode": "mandatory_auto",
    "on_play_mode": "noop",
    "on_enter_mode": "auto",
    "on_activate_mode": "auto",
    "triggered_effects": [
        {
            "trigger": {
                "event": "on_this_card_kills_in_battle",
                "frequency": "each_time",
            },
            "target": {"type": "source_card"},
                "selection_mode": "prompt",
                "cancel_behavior": "abort_step",
                "target_policy": "optional_resolve",
                "selection_mode": "prompt",
                "cancel_behavior": "abort_step",
            "effect": {"action": "remove_sin", "amount": 2, "target_player": "me"},
        },
        {
            "trigger": {
                "event": "on_this_card_kills_in_battle",
                "frequency": "each_time",
            },
            "target": {
                "type": "cards_controlled_by_owner",
                "zone": "graveyard",
                "owner": "me",
                "card_filter": {"card_type_in": ["santo"], "strength_lte": 6},
                "target_policy": "optional_resolve",
                "selection_mode": "prompt",
                "cancel_behavior": "abort_step",
            },
            "effect": {"action": "choose_targets_and_summon_to_field", "min_targets": 1, "max_targets": 1},
                "placement_policy": "prompt_slot_required",
        },
    ],
    "on_play_actions": [],
}


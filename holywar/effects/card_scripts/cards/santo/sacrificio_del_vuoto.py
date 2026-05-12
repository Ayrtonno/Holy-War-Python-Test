from __future__ import annotations

CARD_NAME = """Sacrificio del Vuoto"""

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
            "trigger": {"event": "on_enter_field", "frequency": "each_time"},
            "condition": {"event_card_name_is": "Sacrificio del Vuoto"},
            "target": {
                "type": "cards_controlled_by_owner",
                "zone": "excommunicated",
                "owner": "me",
                "target_policy": "optional_resolve",
                "selection_mode": "prompt",
                "cancel_behavior": "abort_step",
            },
            "effect": {"action": "choose_targets", "min_targets": 0, "max_targets": 1},
        },
        {
            "trigger": {"event": "on_enter_field", "frequency": "each_time"},
            "condition": {"event_card_name_is": "Sacrificio del Vuoto"},
            "target": {
                "type": "selected_target",
                "zone": "excommunicated",
                "owner": "me",
                "min_targets": 0,
                "max_targets": 1,
                "target_policy": "optional_resolve",
                "selection_mode": "prompt",
                "cancel_behavior": "abort_step",
            },
            "effect": {"action": "move_to_relicario"},
        },
        {
            "trigger": {"event": "on_enter_field", "frequency": "each_time"},
            "condition": {"event_card_name_is": "Sacrificio del Vuoto"},
            "target": {
                "type": "selected_target",
                "zone": "deck",
                "owner": "me",
                "min_targets": 0,
                "max_targets": 1,
                "target_policy": "optional_resolve",
                "selection_mode": "prompt",
                "cancel_behavior": "abort_step",
            },
            "effect": {"action": "shuffle_target_owner_decks"},
        },
        {
            "trigger": {"event": "on_card_excommunicated", "frequency": "each_time"},
            "target": {"type": "source_card"},
                "selection_mode": "prompt",
                "cancel_behavior": "abort_step",
                "target_policy": "optional_resolve",
                "selection_mode": "prompt",
                "cancel_behavior": "abort_step",
            "effect": {"action": "increase_strength", "amount": 1},
        },
    ],
    "on_play_actions": [],
}


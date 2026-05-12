from __future__ import annotations

CARD_NAME = """Vucub-Came"""

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
                "event": "on_enter_field",
                "frequency": "each_time",
                "condition": {
                    "all_of": [
                        {"event_card_name_is": "Vucub-Came"},
                        {"payload_from_zone_in": ["graveyard"]},
                    ]
                },
            },
            "target": {
                "type": "cards_controlled_by_owner",
                "zone": "field",
                "owner": "me",
                "card_filter": {"card_type_in": ["santo", "token"]},
                "target_policy": "optional_resolve",
                "selection_mode": "prompt",
                "cancel_behavior": "abort_step",
            },
            "effect": {"action": "increase_faith", "amount": 2},
        },
        {
            "trigger": {
                "event": "on_enter_field",
                "frequency": "each_time",
                "condition": {
                    "all_of": [
                        {"event_card_name_is": "Vucub-Came"},
                        {"payload_from_zone_in": ["graveyard"]},
                    ]
                },
            },
            "target": {
                "type": "cards_controlled_by_owner",
                "zone": "field",
                "owner": "me",
                "card_filter": {"card_type_in": ["santo", "token"]},
                "target_policy": "optional_resolve",
                "selection_mode": "prompt",
                "cancel_behavior": "abort_step",
            },
            "effect": {"action": "increase_strength", "amount": 2},
        },
    ],
    "on_play_actions": [],
}

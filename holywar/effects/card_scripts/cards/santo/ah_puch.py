from __future__ import annotations

CARD_NAME = """Ah Puch"""

SCRIPT = {
    "default_selection_mode": "prompt",
    "default_cancel_behavior": "abort_step",
    "default_target_policy": "optional_resolve",
    "default_placement_policy": "prompt_slot_required",
    "default_activation_mode": "mandatory_auto",
    "on_play_mode": "scripted",
    "on_enter_mode": "auto",
    "on_activate_mode": "auto",
    "triggered_effects": [
        {
            "trigger": {
                "event": "on_card_sent_to_graveyard",
                "frequency": "each_turn",
                "condition": {
                    "payload_from_zone_in": ["attack", "defense"],
                    "event_card_type_in": ["santo", "token"],
                },
            },
            "target": {
                "type": "cards_controlled_by_owner",
                "zone": "field",
                "owner": "me",
                "card_filter": {"name_contains": "Ah Puch"},
                "target_policy": "optional_resolve",
                "selection_mode": "prompt",
                "cancel_behavior": "abort_step",
            },
            "effect": {
                "action": "increase_faith",
                "amount": 1,
            },
        },
        {
            "trigger": {
                "event": "on_card_sent_to_graveyard",
                "frequency": "each_turn",
                "condition": {
                    "payload_from_zone_in": ["attack", "defense"],
                    "event_card_type_in": ["santo", "token"],
                },
            },
            "target": {
                "type": "cards_controlled_by_owner",
                "zone": "field",
                "owner": "me",
                "card_filter": {"name_contains": "Ah Puch"},
                "target_policy": "optional_resolve",
                "selection_mode": "prompt",
                "cancel_behavior": "abort_step",
            },
            "effect": {
                "action": "increase_strength",
                "amount": 1,
            },
        },
    ],
    "on_play_actions": [],
}

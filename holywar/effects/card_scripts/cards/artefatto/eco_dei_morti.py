from __future__ import annotations

CARD_NAME = "Eco dei Morti"

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
                "frequency": "each_time",
                "condition": {
                    "event_card_owner": "me",
                    "event_card_type_in": ["santo"],
                    "payload_from_zone_in": ["attack"],
                },
            },
            "target": {"type": "source_card"},
            "effect": {
                "action": "summon_generated_token",
                "card_name": "Spirito Vacuo",
                "owner": "me",
                "zone": "attack",
                "target_policy": "optional_resolve",
                "selection_mode": "prompt",
                "cancel_behavior": "abort_step",
            },
        },
        {
            "trigger": {
                "event": "on_card_sent_to_graveyard",
                "frequency": "each_time",
                "condition": {
                    "event_card_owner": "me",
                    "event_card_type_in": ["santo"],
                    "payload_from_zone_in": ["defense"],
                },
            },
            "target": {"type": "source_card"},
            "effect": {
                "action": "summon_generated_token",
                "card_name": "Spirito Vacuo",
                "owner": "me",
                "zone": "defense",
                "target_policy": "optional_resolve",
                "selection_mode": "prompt",
                "cancel_behavior": "abort_step",
            },
        },
    ],
    "on_play_actions": [],
}

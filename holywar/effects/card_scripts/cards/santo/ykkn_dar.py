from __future__ import annotations

CARD_NAME = "Ykknødar"

SCRIPT = {
    "on_play_mode": "noop",
    "on_enter_mode": "auto",
    "on_activate_mode": "auto",
    "can_play_from_hand": False,
    "protection_rules": [
        {
            "event": "destroy_by_effect",
            "source_owner": "any",
            "target_owner": "friendly",
            "target_card_types": ["santo", "token"],
            "target_name_contains": "Ykknødar",
        }
    ],
    "triggered_effects": [
        {
            "trigger": {"event": "on_enter_field", "frequency": "each_time"},
            "condition": {"event_card_name_is": "Ykknødar"},
            "target": {"type": "source_card"},
            "effect": {"action": "prevent_specific_card_from_attacking", "amount": 1},
        },
        {
            "trigger": {"event": "on_my_turn_start", "frequency": "each_turn"},
            "target": {"type": "source_card"},
            "effect": {"action": "prevent_specific_card_from_attacking", "amount": 1},
        },
        {
            "trigger": {
                "event": "on_card_drawn",
                "frequency": "each_time",
                "condition": {"event_card_owner": "opponent"},
            },
            "target": {"type": "source_card"},
            "effect": {"action": "remove_sin", "amount": 3, "target_player": "me"},
        },
    ],
    "on_play_actions": [],
}


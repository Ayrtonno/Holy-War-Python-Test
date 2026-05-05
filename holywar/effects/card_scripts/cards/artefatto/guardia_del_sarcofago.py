from __future__ import annotations

CARD_NAME = "Guardia del Sarcofago"

SCRIPT = {
    "on_play_mode": "scripted",
    "on_enter_mode": "auto",
    "on_activate_mode": "auto",
    "triggered_effects": [
        {
            "trigger": {
                "event": "on_attack_declared",
                "frequency": "each_turn",
                "condition": {
                    "all_of": [
                        {"event_card_owner": "opponent"},
                        {"payload_target_slot_is_set": False},
                    ]
                },
            },
            "target": {"type": "source_card"},
            "effect": {
                "action": "set_attack_shield_this_turn",
                "target_player": "me",
                "usage_limit_per_turn": 1,
            },
        },
        {
            "trigger": {
                "event": "on_attack_declared",
                "frequency": "each_turn",
                "condition": {
                    "all_of": [
                        {"event_card_owner": "opponent"},
                        {"payload_target_slot_is_set": False},
                    ]
                },
            },
            "target": {"type": "source_card"},
            "effect": {"action": "decrease_faith", "amount": 2, "usage_limit_per_turn": 1},
        },
        {
            "trigger": {
                "event": "on_attack_declared",
                "frequency": "each_turn",
                "condition": {
                    "all_of": [
                        {"event_card_owner": "opponent"},
                        {"payload_target_slot_is_set": False},
                        {"target_current_faith_lte": 0},
                    ]
                },
            },
            "target": {"type": "source_card"},
            "effect": {"action": "send_to_graveyard", "usage_limit_per_turn": 1},
        },
    ],
    "on_play_actions": [],
}

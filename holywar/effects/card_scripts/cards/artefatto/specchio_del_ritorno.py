from __future__ import annotations

CARD_NAME = "Specchio del Ritorno"

SCRIPT = {
    "on_play_mode": "scripted",
    "on_enter_mode": "auto",
    "on_activate_mode": "auto",
    "play_targeting": "none",
    "triggered_effects": [
        {
            "trigger": {
                "event": "on_this_card_deals_damage",
                "frequency": "each_time",
                "condition": {
                    "all_of": [
                        {"event_card_owner": "opponent"},
                        {"payload_target_owner": "me"},
                    ]
                },
            },
            "target": {"type": "source_card"},
            "effect": {
                "action": "retaliate_event_damage_divided_to_event_source_if_enemy_saint",
                "divisor": 2,
            },
        }
    ],
    "on_play_actions": [],
}

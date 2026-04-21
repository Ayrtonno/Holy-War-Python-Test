from __future__ import annotations

CARD_NAME = "Stalagmiti"

SCRIPT = {
    "on_play_mode": "scripted",
    "on_enter_mode": "auto",
    "on_activate_mode": "auto",
    "triggered_effects": [
        {
            "trigger": {
                "event": "on_this_card_receives_damage",
            },
            "target": {
                "type": "source_card",
            },
            "effect": {
                "action": "retaliate_damage_to_event_source_if_enemy_saint",
                "amount": 3,
            },
        },
    ],
    "on_play_actions": [],
}

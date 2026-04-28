from __future__ import annotations

CARD_NAME = 'Muraglia'

SCRIPT = {
    "on_play_mode": "scripted",
    "on_enter_mode": "auto",
    "on_activate_mode": "auto",
    "play_targeting": "none",
    "triggered_effects": [],
    "on_play_actions": [
        {
            "target": {"type": "source_card"},
            "effect": {"action": "set_attack_shield_this_turn", "target_player": "me"},
        },
    ],
}

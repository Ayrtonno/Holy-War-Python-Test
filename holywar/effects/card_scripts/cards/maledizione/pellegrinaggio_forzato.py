from __future__ import annotations

CARD_NAME = 'Pellegrinaggio Forzato'

SCRIPT = {
    "on_play_mode": "scripted",
    "on_enter_mode": "auto",
    "on_activate_mode": "auto",
    "play_targeting": "none",
    "triggered_effects": [],
    "on_play_actions": [
        {
            "target": {"type": "source_card"},
            "effect": {"action": "swap_attack_defense_rows", "target_player": "opponent"},
        },
    ],
}

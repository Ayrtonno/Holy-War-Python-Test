from __future__ import annotations

CARD_NAME = 'Vilipendio'

SCRIPT = {
    "on_play_mode": "scripted",
    "on_enter_mode": "auto",
    "on_activate_mode": "auto",
    "play_requirements": {"opponent_sin_lte": 50},
    "triggered_effects": [],
    "on_play_actions": [
        {
            "target": {"type": "source_card"},
            "effect": {"action": "inflict_sin", "amount": 15, "target_player": "opponent"},
        },
    ],
}

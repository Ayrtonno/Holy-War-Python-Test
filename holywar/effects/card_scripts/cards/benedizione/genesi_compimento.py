from __future__ import annotations

CARD_NAME = 'Genesi: Compimento'

SCRIPT = {
    "on_play_mode": "scripted",
    "on_enter_mode": "auto",
    "on_activate_mode": "auto",
    "play_targeting": "none",
    "play_requirements": {
        "controller_has_saint_with_name": "Custode della Creazione",
    },
    "triggered_effects": [],
    "on_play_actions": [
        {"target": {"type": "source_card"}, "effect": {"action": "win_the_game", "target_player": "me"}},
    ],
}

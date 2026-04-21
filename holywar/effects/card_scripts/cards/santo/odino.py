from __future__ import annotations

CARD_NAME = """Odino"""

SCRIPT = {
    "on_play_mode": "noop",
    "on_enter_mode": "auto",
    "on_activate_mode": "auto",
    "strength_bonus_rules": [
        {"artifact_name": "Gungnir", "self_bonus": 4},
    ],
    "strength_gain_on_damage_to_enemy_saint": 1,
    "strength_gain_on_lethal_to_enemy_saint": 2,
    "triggered_effects": [],
    "on_play_actions": [],
}


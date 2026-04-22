from __future__ import annotations

CARD_NAME = """Pianta Carnivora"""

SCRIPT = {
    "on_play_mode": "scripted",
    "on_enter_mode": "auto",
    "on_activate_mode": "auto",
    "strength_bonus_rules": [
        {
            "if_card_name": "Pianta Carnivora",
            "controller_has_card_with_name": "Insetto della Palude",
            "controller_has_card_zone": "field",
            "self_bonus": 2,
        }
    ],
    "faith_bonus_rules": [
        {
            "if_card_name": "Pianta Carnivora",
            "controller_has_card_with_name": "Insetto della Palude",
            "controller_has_card_zone": "field",
            "self_bonus": 2,
        }
    ],
    "triggered_effects": [
    ],
    "on_play_actions": [],
}
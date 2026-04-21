from __future__ import annotations

CARD_NAME = """Giorno 6: Creature di Terra"""

SCRIPT = {
    "on_play_mode": "scripted",
    "on_enter_mode": "auto",
    "on_activate_mode": "auto",
    "attack_requirements": {
        "my_inspiration_lte": 4,
    },
    "attack_blocked_message": "Giorno 6 puo attaccare solo se la tua Ispirazione rimanente e inferiore a 5.",
    "triggered_effects": [],
    "on_play_actions": [],
}

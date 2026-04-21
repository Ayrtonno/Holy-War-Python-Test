from __future__ import annotations

CARD_NAME = """Giorno 5: Creature del Mare"""

SCRIPT = {
    "on_play_mode": "scripted",
    "on_enter_mode": "auto",
    "on_activate_mode": "auto",
    "attack_requirements": {
        "my_inspiration_gte": 3,
    },
    "attack_blocked_message": "Giorno 5 puo attaccare solo se la tua Ispirazione rimanente e superiore a 2.",
    "triggered_effects": [],
    "on_play_actions": [],
}

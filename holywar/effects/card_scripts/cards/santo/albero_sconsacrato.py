from __future__ import annotations

CARD_NAME = """Albero Sconsacrato"""

SCRIPT = {
    "on_play_mode": "noop",
    "on_enter_mode": "auto",
    "on_activate_mode": "auto",
    "play_targeting": "none",
    "battle_excommunicate_on_lethal": True,
    "triggered_effects": [
        {
            "trigger": {"event": "on_my_turn_start", "frequency": "each_turn"},
            "target": {"type": "source_card"},
            "effect": {"action": "add_inspiration", "amount": 2, "target_player": "me"},
        }
    ],
    "on_play_actions": [],
}

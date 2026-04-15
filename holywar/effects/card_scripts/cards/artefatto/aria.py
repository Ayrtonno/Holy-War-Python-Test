from __future__ import annotations

CARD_NAME = """Aria"""

SCRIPT = {
    "on_play_mode": "scripted",
    "on_enter_mode": "auto",
    "on_activate_mode": "auto",
    "triggered_effects": [
        {
            "trigger": {"event": "on_main_phase_start", "frequency": "each_turn"},
            "target": {"type": "cards_controlled_by_owner", "zone": "field", "owner": "me"},
            "effect": {"action": "add_inspiration", "amount": 1, "target_player": "me"}
        }
    ],
    "on_play_actions": [],
}


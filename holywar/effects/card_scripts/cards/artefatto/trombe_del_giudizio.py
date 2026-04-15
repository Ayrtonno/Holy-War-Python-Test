from __future__ import annotations

CARD_NAME = """Trombe del Giudizio"""

SCRIPT = {
    "on_play_mode": "scripted",
    "on_enter_mode": "auto",
    "on_activate_mode": "auto",
    "triggered_effects": [
        {
            "trigger": {"event": "on_my_turn_start", "frequency": "each_turn"},
            "target": {"type": "cards_controlled_by_owner", "zone": "field", "owner": "me"},
            "effect": {"action": "trombe_del_giudizio_tick"}
        }
    ],
    "on_play_actions": [],
}


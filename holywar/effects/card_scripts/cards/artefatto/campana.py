from __future__ import annotations

CARD_NAME = """Campana"""

SCRIPT = {
    "on_play_mode": "scripted",
    "on_enter_mode": "auto",
    "on_activate_mode": "auto",
    "triggered_effects": [
        {
            "trigger": {"event": "on_saint_defeated_or_destroyed", "frequency": "each_turn"},
            "target": {"type": "cards_controlled_by_owner", "zone": "field", "owner": "me"},
            "effect": {"action": "campana_add_counter"}
        }
    ],
    "on_play_actions": [],
}


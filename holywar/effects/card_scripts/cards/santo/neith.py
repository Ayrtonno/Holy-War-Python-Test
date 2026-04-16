from __future__ import annotations

CARD_NAME = """Neith"""

SCRIPT = {
    "on_play_mode": "noop",
    "on_enter_mode": "auto",
    "on_activate_mode": "auto",
    "triggered_effects": [
        {
            "trigger": {"event": "on_enter_field", "frequency": "each_turn"},
            "target": {
                "type": "cards_controlled_by_owner",
                "zone": "field",
                "owner": "opponent",
                "card_filter": {"card_type_in": ["santo", "token"]},
            },
            "effect": {"action": "decrease_faith", "amount": 1},
        }
    ],
    "on_play_actions": [],
}

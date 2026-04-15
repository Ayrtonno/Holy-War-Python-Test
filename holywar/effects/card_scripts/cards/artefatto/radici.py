from __future__ import annotations

CARD_NAME = "Radici"

SCRIPT = {
    "on_play_mode": "scripted",
    "on_enter_mode": "auto",
    "on_activate_mode": "auto",
    "triggered_effects": [
        {
            "trigger": {"event": "on_my_turn_start", "frequency": "each_turn"},
            "target": {
                "type": "cards_controlled_by_owner",
                "zone": "field",
                "owner": "me",
                "card_filter": {"name_contains": "albero", "card_type_in": ["santo", "token"]},
            },
            "effect": {"action": "increase_faith", "amount": 2},
        }
    ],
    "on_play_actions": [],
}

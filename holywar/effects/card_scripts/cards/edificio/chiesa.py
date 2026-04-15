from __future__ import annotations

CARD_NAME = "Chiesa"

SCRIPT = {
    "on_play_mode": "scripted",
    "on_enter_mode": "auto",
    "on_activate_mode": "auto",
    "triggered_effects": [
        {
            "trigger": {
                "event": "on_card_drawn",
                "frequency": "each_turn",
                "condition": {"event_card_owner": "me"},
            },
            "target": {"type": "cards_controlled_by_owner", "zone": "field", "owner": "me", "card_filter": {"card_type_in": ["santo", "token"]}},
            "effect": {"action": "increase_faith", "amount": 2},
        }
    ],
    "on_play_actions": [],
}

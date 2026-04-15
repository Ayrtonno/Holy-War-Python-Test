from __future__ import annotations

CARD_NAME = "Saga degli Eroi Caduti"

SCRIPT = {
    "on_play_mode": "scripted",
    "on_enter_mode": "auto",
    "on_activate_mode": "auto",
    "triggered_effects": [
        {
            "trigger": {
                "event": "on_saint_defeated_or_destroyed",
                "frequency": "each_turn",
                "condition": {"event_card_owner": "me"},
            },
            "target": {
                "type": "cards_controlled_by_owner",
                "zone": "field",
                "owner": "me",
                "card_filter": {"card_type_in": ["santo", "token"], "exclude_event_card": True},
            },
            "effect": {"action": "increase_strength", "amount": 1},
        }
    ],
    "on_play_actions": [],
}

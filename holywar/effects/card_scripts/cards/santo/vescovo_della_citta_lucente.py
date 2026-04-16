from __future__ import annotations

CARD_NAME = "Vescovo della Città Lucente"

SCRIPT = {
    "on_play_mode": "noop",
    "on_enter_mode": "scripted",
    "on_activate_mode": "auto",
    "play_targeting": "none",
    "triggered_effects": [],
    "on_play_actions": [],
    "on_enter_actions": [
        {
            "target": {
                "type": "cards_controlled_by_owner",
                "zone": "field",
                "owner": "me",
                "card_filter": {"card_type_in": ["santo", "token"]},
            },
            "condition": {"target_is_damaged": True},
            "effect": {"action": "increase_faith_if_damaged", "amount": 5},
        }
    ],
}

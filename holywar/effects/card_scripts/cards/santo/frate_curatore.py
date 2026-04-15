from __future__ import annotations

CARD_NAME = "Frate Curatore"

SCRIPT = {
    "on_play_mode": "scripted",
    "on_enter_mode": "auto",
    "on_activate_mode": "auto",
    "triggered_effects": [
        {
            "trigger": {"event": "on_opponent_draws", "frequency": "each_turn"},
            "target": {"type": "cards_controlled_by_owner", "zone": "field", "owner": "me", "card_filter": {"card_type_in": ["santo", "token"]}},
            "effect": {"action": "increase_faith", "amount": 1},
        }
    ],
    "on_play_actions": [],
}

from __future__ import annotations

CARD_NAME = "Altare delle Otto Reliquie"

SCRIPT = {
    "on_play_mode": "scripted",
    "on_enter_mode": "auto",
    "on_activate_mode": "auto",
    "play_targeting": "none",
    "triggered_effects": [
        {
            "trigger": {"event": "on_card_drawn", "frequency": "each_time", "condition": {"event_card_owner": "me"}},
            "target": {"type": "cards_controlled_by_owner", "zone": "field", "owner": "me", "card_filter": {"name_contains": "ba xian", "card_type_in": ["santo", "token"]}},
            "effect": {"action": "increase_faith", "amount": 1},
        },
        {
            "trigger": {"event": "on_card_drawn", "frequency": "each_time", "condition": {"event_card_owner": "me"}},
            "target": {"type": "cards_controlled_by_owner", "zone": "field", "owner": "me", "card_filter": {"name_contains": "ba xian", "card_type_in": ["santo", "token"]}},
            "effect": {"action": "increase_strength", "amount": 1},
        },
    ],
    "on_play_actions": [],
}

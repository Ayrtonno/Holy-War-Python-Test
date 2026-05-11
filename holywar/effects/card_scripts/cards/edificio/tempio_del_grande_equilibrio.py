from __future__ import annotations

CARD_NAME = "Tempio del Grande Equilibrio"

SCRIPT = {
    "on_play_mode": "scripted",
    "on_enter_mode": "auto",
    "on_activate_mode": "scripted",
    "play_targeting": "none",
    "activate_targeting": "none",
    "triggered_effects": [
        {
            "trigger": {
                "event": "on_card_played",
                "frequency": "each_time",
                "condition": {"event_card_type_in": ["benedizione", "maledizione"]},
            },
            "target": {"type": "source_card"},
            "effect": {"action": "campana_add_counter"},
        }
    ],
    "on_play_actions": [],
    "on_activate_actions": [
        {
            "condition": {"source_counter_gte": 3},
            "target": {"type": "source_card"},
            "effect": {"action": "campana_remove_counter", "amount": 3},
        },
        {
            "condition": {"source_counter_gte": 3},
            "effect": {"action": "draw_cards", "amount": 1, "target_player": "me"},
        },
        {
            "condition": {"source_counter_gte": 3},
            "effect": {"action": "mill_cards", "amount": 1, "target_player": "opponent"},
        },
    ],
}

from __future__ import annotations

CARD_NAME = "Monaco della Bilancia"

SCRIPT = {
    "on_play_mode": "scripted",
    "on_enter_mode": "auto",
    "on_activate_mode": "auto",
    "play_targeting": "none",
    "triggered_effects": [],
    "on_play_actions": [
        {
            "target": {"type": "source_card"},
            "effect": {"action": "mill_top_and_store_card_type", "target_player": "me", "store_as": "monaco_my_type"},
        },
        {
            "target": {"type": "source_card"},
            "effect": {"action": "mill_top_and_store_card_type", "target_player": "opponent", "store_as": "monaco_opp_type"},
        },
        {
            "target": {"type": "source_card"},
            "effect": {
                "action": "draw_if_stored_values_not_equal",
                "flag": "monaco_my_type",
                "stored": "monaco_opp_type",
                "target_player": "me",
                "amount": 1,
            },
        },
    ],
}

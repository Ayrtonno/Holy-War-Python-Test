from __future__ import annotations

CARD_NAME = "Vaso della Corrente Mite"

SCRIPT = {
    "on_play_mode": "scripted",
    "on_enter_mode": "auto",
    "on_activate_mode": "scripted",
    "activate_once_per_turn": True,
    "play_targeting": "none",
    "activate_targeting": "guided",
    "triggered_effects": [],
    "on_play_actions": [],
    "on_activate_actions": [
        {
            "target": {
                "type": "selected_target",
                "zone": "hand",
                "owner": "me",
                "min_targets": 1,
                "max_targets": 1,
            },
            "effect": {"action": "send_to_graveyard"},
        },
        {"effect": {"action": "draw_cards", "amount": 1, "target_player": "me"}},
        {"effect": {"action": "mill_cards", "amount": 1, "target_player": "opponent"}},
    ],
}

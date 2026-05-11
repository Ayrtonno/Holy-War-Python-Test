from __future__ import annotations

CARD_NAME = "Vuoto Fecondo"

SCRIPT = {
    "on_play_mode": "scripted",
    "on_enter_mode": "auto",
    "on_activate_mode": "auto",
    "play_targeting": "guided",
    "triggered_effects": [],
    "on_play_actions": [
        {
            "target": {
                "type": "selected_target",
                "zone": "graveyard",
                "owner": "me",
                "card_filter": {"card_type_in": ["benedizione", "maledizione"]},
                "min_targets": 1,
                "max_targets": 1,
            },
            "effect": {"action": "move_to_hand"},
        },
        {
            "effect": {"action": "mill_cards", "amount": 1, "target_player": "opponent"},
        },
    ],
}

from __future__ import annotations

CARD_NAME = "Il Grande Sacrificio"

SCRIPT = {
    "on_play_mode": "scripted",
    "on_enter_mode": "auto",
    "on_activate_mode": "auto",
    "play_targeting": "guided",
    "triggered_effects": [],
    "on_play_actions": [
        {
            "target": {
                "type": "selected_targets",
                "owner": "me",
                "zone": "relicario",
                "card_filter": {},
                "min_targets": 3,
                "max_targets": 3,
            },
            "effect": {"action": "move_to_graveyard"},
        },
        {
            "target": {"type": "source_card"},
            "effect": {"action": "remove_sin", "amount": 5, "target_player": "me"},
        },
    ],
}

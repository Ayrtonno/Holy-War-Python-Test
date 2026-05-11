from __future__ import annotations

CARD_NAME = "Debito degli Eccessi"

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
                "zone": "hand",
                "owner": "opponent",
                "min_targets": 1,
                "max_targets": 1,
            },
            "effect": {"action": "send_to_graveyard"},
        },
        {"effect": {"action": "draw_cards", "amount": 1, "target_player": "me"}},
    ],
}

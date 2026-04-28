from __future__ import annotations

CARD_NAME = 'Furia di Llakhnal'

SCRIPT = {
    "on_play_mode": "scripted",
    "on_enter_mode": "auto",
    "on_activate_mode": "auto",
    "play_targeting": "none",
    "play_requirements": {
        "all_of": [
            {"my_sin_lte": 49},
            {"opponent_sin_lte": 49},
        ]
    },
    "triggered_effects": [],
    "on_play_actions": [
        {
            "target": {"type": "source_card"},
            "effect": {"action": "inflict_sin", "amount": 15, "target_player": "me"},
        },
        {
            "target": {"type": "source_card"},
            "effect": {"action": "inflict_sin", "amount": 15, "target_player": "opponent"},
        },
        {
            "target": {"type": "source_card"},
            "effect": {"action": "excommunicate_card_no_sin"},
        },
    ],
}

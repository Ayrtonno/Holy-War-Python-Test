from __future__ import annotations

CARD_NAME = "Piaga: Rane Invasive"

SCRIPT = {
    "on_play_mode": "scripted",
    "on_enter_mode": "auto",
    "on_activate_mode": "auto",
    "play_targeting": "none",
    "triggered_effects": [],
    "on_play_actions": [
        {
            "target": {"type": "source_card"},
            "effect": {"action": "inflict_sin", "amount": 6, "target_player": "opponent"},
        },
        {
            "target": {"type": "source_card"},
            "effect": {
                "action": "optional_recover_matching_then_shuffle",
                "from_zone": "graveyard",
                "to_zone": "hand",
                "card_name": "Piaga",
                "amount": 1,
                "shuffle_after": False,
            },
        },
        {
            "target": {"type": "source_card"},
            "effect": {"action": "inflict_sin", "amount": 1, "target_player": "me"},
        },
    ],
}

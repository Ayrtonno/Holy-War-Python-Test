from __future__ import annotations

CARD_NAME = "Grandi Costruzioni"

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
                "owner": "me",
                "zone": "relicario",
                "zones": ["relicario", "graveyard"],
                "card_filter": {"card_type_in": ["artefatto"]},
                "min_targets": 1,
                "max_targets": 1,
            },
            "effect": {"action": "summon_named_card"},
        },
    ],
}

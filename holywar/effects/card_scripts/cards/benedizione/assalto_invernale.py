from __future__ import annotations

CARD_NAME = "Assalto Invernale"

SCRIPT = {
    "on_play_mode": "scripted",
    "on_enter_mode": "auto",
    "on_activate_mode": "auto",
    "play_targeting": "guided",
    "play_requirements": {
        "controller_saints_sent_to_graveyard_this_turn_gte": 3,
    },
    "triggered_effects": [],
    "on_play_actions": [
        {
            "target": {
                "type": "selected_target",
                "owner": "me",
                "zone": "graveyard",
                "zones": ["graveyard", "deck"],
                "card_filter": {
                    "name_in": ["Fenrir", "Jormungandr"],
                },
                "min_targets": 1,
                "max_targets": 1,
            },
            "effect": {
                "action": "summon_named_card",
            },
        },
    ],
}

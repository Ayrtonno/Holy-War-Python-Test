from __future__ import annotations

CARD_NAME = """Loki"""

SCRIPT = {
    "on_play_mode": "noop",
    "on_enter_mode": "auto",
    "on_activate_mode": "scripted",
    "play_targeting": "none",
    "activate_targeting": "guided",
    "triggered_effects": [],
    "on_play_actions": [],
    "on_activate_actions": [
        {
            "target": {"type": "source_card"},
            "effect": {"action": "remove_from_board_no_sin"},
        },
        {
            "target": {
                "type": "selected_target",
                "owner": "me",
                "zones": ["hand"],
                "card_filter": {
                    "card_type_in": ["santo"],
                    "name_in": ["Fenrir", "Jormungandr"],
                },
                "min_targets": 1,
                "max_targets": 1,
            },
            "effect": {"action": "summon_card_from_hand"},
        },
    ],
}


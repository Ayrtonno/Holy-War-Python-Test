from __future__ import annotations

CARD_NAME = """Muninn"""

SCRIPT = {
    "on_play_mode": "noop",
    "play_targeting": "none",
    "on_enter_mode": "scripted",
    "on_activate_mode": "auto",
    "triggered_effects": [],
    "on_play_actions": [],
    "on_enter_actions": [
        {
            "effect": {
                "action": "optional_recover_cards",
                "target_player": "me",
                "from_zone": "graveyard",
                "min_targets": 0,
                "max_targets": 1,
                "to_zone": "relicario",
                "to_zone_if_condition": {
                    "controller_has_cards": {
                        "owner": "me",
                        "zones": ["field"],
                        "card_filter": {"card_type_in": ["santo"], "name_equals": "Odino"},
                        "min_count": 1,
                    }
                },
                "to_zone_if": "hand",
                "shuffle_after": True,
            },
        },
    ],
}

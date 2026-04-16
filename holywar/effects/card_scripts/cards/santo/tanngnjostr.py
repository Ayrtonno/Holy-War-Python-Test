from __future__ import annotations

CARD_NAME = """Tanngnjostr"""

SCRIPT = {
    "on_play_mode": "noop",
    "on_enter_mode": "auto",
    "on_activate_mode": "scripted",
    "play_targeting": "none",
    "activate_targeting": "none",
    "triggered_effects": [],
    "on_play_actions": [],
    "on_activate_actions": [
        {
            "condition": {"controller_has_saint_with_name": "Thor"},
            "target": {
                "type": "cards_controlled_by_owner",
                "zone": "field",
                "owner": "me",
                "card_filter": {"name_contains": "Thor", "card_type_in": ["santo", "token"]},
            },
            "effect": {"action": "increase_faith", "amount": 4},
        },
        {
            "condition": {"controller_has_saint_with_name": "Thor"},
            "target": {"type": "source_card"},
            "effect": {"action": "remove_from_board_no_sin"},
        },
    ],
}


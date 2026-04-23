from __future__ import annotations

CARD_NAME = 'Settimo Sigillo'

SCRIPT = {
    "on_play_mode": "scripted",
    "on_enter_mode": "auto",
    "on_activate_mode": "auto",
    "play_targeting": "none",
    "triggered_effects": [],
    "on_play_actions": [
        {
            "target": {
                "type": "cards_controlled_by_owner",
                "zone": "deck",
                "owner": "me",
                "card_filter": {"name_contains": "Giorno"},
            },
            "effect": {"action": "choose_targets", "min_targets": 0, "max_targets": 2},
        },
        {
            "target": {
                "type": "selected_targets",
                "zone": "deck",
                "owner": "me",
                "card_filter": {"name_contains": "Giorno"},
                "min_targets": 0,
                "max_targets": 2,
            },
            "effect": {"action": "move_to_hand"},
        },
        {
            "target": {"type": "source_card"},
            "effect": {"action": "shuffle_deck", "target_player": "me"},
        },
    ],
}

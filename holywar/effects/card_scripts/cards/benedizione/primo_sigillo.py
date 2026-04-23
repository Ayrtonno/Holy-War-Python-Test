from __future__ import annotations

CARD_NAME = 'Primo Sigillo'

SCRIPT = {
    "on_play_mode": "scripted",
    "on_enter_mode": "auto",
    "on_activate_mode": "auto",
    "play_targeting": "none",
    "triggered_effects": [],
    "on_play_actions": [
        {
            "condition": {"controller_has_building_with_name": "Altare dei Sette Sigilli"},
            "target": {"type": "source_card"},
            "effect": {"action": "add_seal_counter", "amount": 2},
        },
        {
            "condition": {"not": {"controller_has_building_with_name": "Altare dei Sette Sigilli"}},
            "target": {
                "type": "cards_controlled_by_owner",
                "zone": "deck",
                "owner": "me",
                "card_filter": {"name_equals": "Altare dei Sette Sigilli"},
                "max_targets": 1,
            },
            "effect": {"action": "move_to_hand"},
        },
        {
            "target": {"type": "source_card"},
            "effect": {"action": "shuffle_deck", "target_player": "me"},
        },
    ],
}

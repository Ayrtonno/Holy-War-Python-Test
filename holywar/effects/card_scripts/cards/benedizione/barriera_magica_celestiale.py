from __future__ import annotations

CARD_NAME = "Barriera Magica Celestiale"

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
                "owner": "me",
                "zone": "hand",
                "max_targets": 1,
            },
            "effect": {"action": "send_to_graveyard"},
        },
        {
            "target": {"type": "source_card"},
            "effect": {"action": "grant_counter_spell", "amount": 1, "target_player": "me"},
        },
        {
            "target": {"type": "source_card"},
            "effect": {"action": "move_source_to_zone", "to_zone": "relicario"},
        },
        {
            "target": {"type": "source_card"},
            "effect": {"action": "shuffle_deck", "target_player": "me"},
        },
    ],
}

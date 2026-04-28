from __future__ import annotations

CARD_NAME = "Dono di Kah"

SCRIPT = {
    "on_play_mode": "scripted",
    "on_enter_mode": "auto",
    "on_activate_mode": "auto",
    "play_targeting": "guided",
    "triggered_effects": [],
    "on_play_actions": [
        {
            "target": {
                "type": "selected_targets",
                "owner": "me",
                "zone": "relicario",
                "card_filter": {"top_n_from_zone": 5},
                "min_targets": 0,
                "max_targets": 5,
            },
            "effect": {"action": "move_to_hand"},
        },
        {
            "target": {
                "type": "selected_targets",
                "owner": "me",
                "zone": "relicario",
                "card_filter": {"top_n_from_zone": 5},
                "min_targets": 0,
                "max_targets": 5,
            },
            "effect": {"action": "pay_inspiration_per_target", "amount": 2, "target_player": "me"},
        },
        {
            "target": {"type": "source_card"},
            "effect": {"action": "shuffle_deck", "target_player": "me"},
        },
    ],
}

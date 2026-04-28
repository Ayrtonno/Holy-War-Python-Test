from __future__ import annotations

CARD_NAME = 'Rinforzi'

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
                "zone": "field",
                "owner": "me",
                "card_filter": {"card_type_in": ["santo", "token"]},
            },
            "effect": {"action": "choose_targets", "min_targets": 2, "max_targets": 2},
        },
        {
            "target": {"type": "source_card"},
            "effect": {"action": "swap_selected_attack_defense"},
        },
    ],
}

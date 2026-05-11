from __future__ import annotations

CARD_NAME = 'Giorno 3: Terre e Mari'

SCRIPT = {
    "on_play_mode": "scripted",
    "on_enter_mode": "auto",
    "on_activate_mode": "auto",
    "play_targeting": "auto",
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
            "target": {"type": "selected_target"},
            "effect": {"action": "swap_selected_attack_defense"},
        },
    ],
}

from __future__ import annotations

CARD_NAME = "Passo delle Nubi Gemelle"

SCRIPT = {
    "on_play_mode": "scripted",
    "on_enter_mode": "auto",
    "on_activate_mode": "auto",
    "play_targeting": "guided",
    "triggered_effects": [],
    "on_play_actions": [
        {
            "target": {
                "type": "selected_target",
                "zone": "hand",
                "owner": "me",
                "card_filter": {"name_contains": "ba xian", "card_type_in": ["santo", "token"]},
                "min_targets": 1,
                "max_targets": 1,
            },
            "effect": {"action": "summon_target_to_field_pay_half_inspiration", "target_player": "me"},
        },
        {"effect": {"action": "mill_cards", "amount": 1, "target_player": "opponent"}},
    ],
}

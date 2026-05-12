from __future__ import annotations

CARD_NAME = "Zhongli Quan"

# Zhongli Quan counts itself for this check while resolving its own play effect.
# Therefore we only need to verify the other 7 Ba Xian names across hand/field/graveyard.
ALL_8_NAMES_PRESENT = {
    "all_of": [
        {"controller_has_cards": {"zones": ["hand", "field", "graveyard"], "owner": "me", "card_filter": {"name_equals": "Lu Dongbin"}, "min_count": 1}},
        {"controller_has_cards": {"zones": ["hand", "field", "graveyard"], "owner": "me", "card_filter": {"name_equals": "He Xian'gu"}, "min_count": 1}},
        {"controller_has_cards": {"zones": ["hand", "field", "graveyard"], "owner": "me", "card_filter": {"name_equals": "Li Tieguai"}, "min_count": 1}},
        {"controller_has_cards": {"zones": ["hand", "field", "graveyard"], "owner": "me", "card_filter": {"name_equals": "Han Xiangzi"}, "min_count": 1}},
        {"controller_has_cards": {"zones": ["hand", "field", "graveyard"], "owner": "me", "card_filter": {"name_equals": "Lan Caihe"}, "min_count": 1}},
        {"controller_has_cards": {"zones": ["hand", "field", "graveyard"], "owner": "me", "card_filter": {"name_equals": "Zhang Guolao"}, "min_count": 1}},
        {"controller_has_cards": {"zones": ["hand", "field", "graveyard"], "owner": "me", "card_filter": {"name_equals": "Cao Guojiu"}, "min_count": 1}},
    ]
}

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
                "zone": "graveyard",
                "owner": "me",
                "card_filter": {"name_contains": "ba xian", "card_type_in": ["santo", "token"]},
                "min_targets": 0,
                "max_targets": 2,
            },
            "effect": {"action": "move_to_hand"},
        },
        {
            "condition": ALL_8_NAMES_PRESENT,
            "effect": {"action": "inflict_sin", "amount": 20, "target_player": "opponent"},
        },
        {
            "condition": ALL_8_NAMES_PRESENT,
            "effect": {"action": "remove_sin", "amount": 20, "target_player": "me"},
        },
    ],
}

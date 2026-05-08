from __future__ import annotations

CARD_NAME = """Fuoco"""
ELEMENT_ARTIFACTS = ["Aria", "Fuoco", "Terra", "Acqua"]
CREATOR_NAME = "Dio, il Creatore"

SCRIPT = {
    "on_play_mode": "scripted",
    "on_enter_mode": "auto",
    "on_activate_mode": "scripted",
    "activate_targeting": "guided",
    "triggered_effects": [
        {
            "trigger": {"event": "on_my_turn_end", "frequency": "each_turn"},
            "target": {
                "type": "all_saints_on_field",
                "card_filter": {"card_type_in": ["santo"], "crosses_gte": 4},
            },
            "effect": {"action": "decrease_faith", "amount": 2},
        }
    ],
    "on_play_actions": [],
    "on_activate_actions": [
        {
            "condition": {
                "all_of": [
                    *[
                        {
                            "controller_has_cards": {
                                "owner": "me",
                                "zone": "field",
                                "card_filter": {"name_equals": name},
                            }
                        }
                        for name in ELEMENT_ARTIFACTS
                    ],
                    {
                        "controller_has_cards": {
                            "owner": "me",
                            "zones": ["hand", "deck"],
                            "card_filter": {"name_equals": CREATOR_NAME, "card_type_in": ["santo"]},
                            "min_count": 1,
                        }
                    },
                ]
            },
            "target": {
                "type": "selected_target",
                "owner": "me",
                "zone": "deck",
                "zones": ["hand", "deck"],
                "card_filter": {"name_equals": CREATOR_NAME, "card_type_in": ["santo"]},
                "min_targets": 1,
                "max_targets": 1,
            },
            "effect": {"action": "summon_named_card"},
        }
    ],
}

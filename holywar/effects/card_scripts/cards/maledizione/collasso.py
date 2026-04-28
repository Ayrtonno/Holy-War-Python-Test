from __future__ import annotations

CARD_NAME = 'Collasso'

SCRIPT = {
    "on_play_mode": "scripted",
    "on_enter_mode": "auto",
    "on_activate_mode": "auto",
    "play_targeting": "none",
    "triggered_effects": [],
    "on_play_actions": [
        {
            "condition": {
                "all_of": [
                    {
                        "controller_has_cards": {
                            "owner": "me",
                            "zone": "building",
                            "min_count": 1,
                        }
                    },
                    {
                        "controller_has_cards": {
                            "owner": "opponent",
                            "zone": "building",
                            "min_count": 1,
                        }
                    },
                ]
            },
            "target": {
                "type": "cards_controlled_by_owner",
                "zone": "field",
                "owner": "me",
                "card_filter": {"card_type_in": ["artefatto"]},
            },
            "effect": {"action": "choose_targets", "min_targets": 1, "max_targets": 1},
        },
        {
            "condition": {
                "all_of": [
                    {
                        "controller_has_cards": {
                            "owner": "me",
                            "zone": "building",
                            "min_count": 1,
                        }
                    },
                    {
                        "controller_has_cards": {
                            "owner": "opponent",
                            "zone": "building",
                            "min_count": 1,
                        }
                    },
                ]
            },
            "target": {"type": "selected_targets"},
            "effect": {"action": "destroy_card"},
        },
        {
            "condition": {
                "all_of": [
                    {
                        "controller_has_cards": {
                            "owner": "me",
                            "zone": "building",
                            "min_count": 1,
                        }
                    },
                    {
                        "controller_has_cards": {
                            "owner": "opponent",
                            "zone": "building",
                            "min_count": 1,
                        }
                    },
                ]
            },
            "target": {
                "type": "cards_controlled_by_owner",
                "zone": "field",
                "owner": "opponent",
                "card_filter": {"card_type_in": ["artefatto"]},
            },
            "effect": {"action": "choose_targets", "min_targets": 1, "max_targets": 1},
        },
        {
            "condition": {
                "all_of": [
                    {
                        "controller_has_cards": {
                            "owner": "me",
                            "zone": "building",
                            "min_count": 1,
                        }
                    },
                    {
                        "controller_has_cards": {
                            "owner": "opponent",
                            "zone": "building",
                            "min_count": 1,
                        }
                    },
                ]
            },
            "target": {"type": "selected_targets"},
            "effect": {"action": "destroy_card"},
        },
    ],
}

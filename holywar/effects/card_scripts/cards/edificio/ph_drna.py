from __future__ import annotations

CARD_NAME = """Ph'drna"""

SCRIPT = {
    "on_play_mode": "scripted",
    "on_enter_mode": "auto",
    "on_activate_mode": "scripted",
    "activate_targeting": "none",
    "can_activate_by_any_player": True,
    "inverts_saint_summon_controller": True,
    "indestructible_except_own_activation": True,
    "triggered_effects": [],
    "on_play_actions": [],
    "on_activate_actions": [
        {
            "target": {"type": "source_card"},
            "effect": {
                "action": "choose_option",
                "choice_title": "Ph'drna",
                "choice_prompt": "Scegli il costo di attivazione.",
                "choice_options": [
                    {
                        "value": "building",
                        "label": "Sacrifica 1 Edificio + 10 Ispirazione",
                        "condition": {
                            "all_of": [
                                {"my_inspiration_gte": 10},
                                {
                                    "controller_has_cards": {
                                        "owner": "me",
                                        "zone": "building",
                                        "min_count": 1,
                                    }
                                },
                            ]
                        },
                    },
                    {
                        "value": "artifacts",
                        "label": "Sacrifica 4 Artefatti + 10 Ispirazione",
                        "condition": {
                            "all_of": [
                                {"my_inspiration_gte": 10},
                                {
                                    "controller_has_cards": {
                                        "owner": "me",
                                        "zone": "artifacts",
                                        "min_count": 4,
                                    }
                                },
                            ]
                        },
                    },
                ],
            },
        },
        {
            "target": {
                "type": "cards_controlled_by_owner",
                "zone": "field",
                "owner": "any",
            },
            "effect": {"action": "choose_targets", "min_targets": 1, "max_targets": 1},
        },
        {
            "target": {"type": "source_card"},
            "effect": {"action": "phdrna_activate_destroy_target_then_self"},
        },
    ],
}

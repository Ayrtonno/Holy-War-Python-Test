from __future__ import annotations

CARD_NAME = "Custode della Creazione"

REQUIRED_DAYS = [
    "Giorno 1: Cieli e Terra",
    "Giorno 2: Cielo Terrestre",
    "Giorno 3: Terre e Mari",
    "Giorno 4: Stelle",
    "Giorno 5: Creature del Mare",
    "Giorno 6: Creature di Terra",
    "Giorno 7: Riposo",
]

SCRIPT = {
    "default_selection_mode": "prompt",
    "default_cancel_behavior": "abort_step",
    "default_target_policy": "optional_resolve",
    "default_placement_policy": "prompt_slot_required",
    "default_activation_mode": "mandatory_auto",
    "on_play_mode": "scripted",
    "on_enter_mode": "auto",
    "on_activate_mode": "auto",
    "play_targeting": "none",
    "protection_rules": [
        {
            "event": "target_by_effect",
            "source_owner": "enemy",
            "target_owner": "friendly",
            "target_names": ["Custode della Creazione"],
        }
    ],
    "play_requirements": {
        "can_play_without_inspiration_cost_if": {
            "all_of": [
                {
                    "controller_has_cards": {
                        "zones": ["field", "graveyard"],
                        "owner": "me",
                        "card_filter": {"name_equals": name},
                    }
                }
                for name in REQUIRED_DAYS
            ]
        },
        "all_of": [
            {
                "controller_has_cards": {
                    "zones": ["field", "graveyard"],
                    "owner": "me",
                    "card_filter": {"name_equals": name},
                }
            }
            for name in REQUIRED_DAYS
        ]
    },
    "triggered_effects": [],
    "on_play_actions": [
        {
            "activation_mode": "mandatory_auto",
            "target": {
                "type": "cards_controlled_by_owner",
                "zones": ["field", "graveyard"],
                "owner": "me",
                "card_filter": {"name_equals": name},
                "max_targets": 1,
                "target_policy": "optional_resolve",
                "selection_mode": "prompt",
                "cancel_behavior": "abort_step",
            },
            "effect": {"action": "excommunicate_card_no_sin"},
        }
        for name in REQUIRED_DAYS
    ],
}

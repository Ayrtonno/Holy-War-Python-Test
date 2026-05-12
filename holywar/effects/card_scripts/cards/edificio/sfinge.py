from __future__ import annotations

CARD_NAME = """Sfinge"""

SCRIPT = {
    "default_selection_mode": "prompt",
    "default_cancel_behavior": "abort_step",
    "default_target_policy": "optional_resolve",
    "default_placement_policy": "prompt_slot_required",
    "default_activation_mode": "mandatory_auto",
    "on_play_mode": "scripted",
    "on_enter_mode": "auto",
    "on_activate_mode": "auto",
    "doubles_enemy_play_cost": True,
    "play_requirements": {
        "all_of": [
            {
                "controller_has_cards": {
                    "owner": "me",
                    "zone": "artifacts",
                    "min_count": 1,
                    "card_filter": {"name_equals": "Piramide: Cheope"},
                }
            },
            {
                "controller_has_cards": {
                    "owner": "me",
                    "zone": "artifacts",
                    "min_count": 1,
                    "card_filter": {"name_equals": "Piramide: Chefren"},
                }
            },
            {
                "controller_has_cards": {
                    "owner": "me",
                    "zone": "artifacts",
                    "min_count": 1,
                    "card_filter": {"name_equals": "Piramide: Micerino"},
                }
            },
        ]
    },
    "triggered_effects": [],
    "on_play_actions": [],
}

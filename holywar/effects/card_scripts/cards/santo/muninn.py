from __future__ import annotations

CARD_NAME = """Muninn"""

SCRIPT = {
    "default_selection_mode": "prompt",
    "default_cancel_behavior": "abort_step",
    "default_target_policy": "optional_resolve",
    "default_placement_policy": "prompt_slot_required",
    "default_activation_mode": "mandatory_auto",
    "on_play_mode": "noop",
    "play_targeting": "none",
    "on_enter_mode": "scripted",
    "on_activate_mode": "auto",
    "triggered_effects": [],
    "on_play_actions": [],
    "on_enter_actions": [
        {
            "activation_mode": "mandatory_auto",
            "effect": {
                "action": "optional_recover_cards",
                "target_player": "me",
                "from_zone": "graveyard",
                "min_targets": 0,
                "max_targets": 1,
                "to_zone": "relicario",
                "to_zone_if_condition": {
                    "controller_has_cards": {
                        "owner": "me",
                        "zones": ["field"],
                        "card_filter": {"card_type_in": ["santo"], "name_equals": "Odino"},
                        "min_count": 1,
                    }
                },
                "to_zone_if": "hand",
                "shuffle_after": True,
            },
        },
    ],
}

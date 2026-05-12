from __future__ import annotations

CARD_NAME = """Custode dei Sigilli"""

SCRIPT = {
    "default_selection_mode": "prompt",
    "default_cancel_behavior": "abort_step",
    "default_target_policy": "optional_resolve",
    "default_placement_policy": "prompt_slot_required",
    "default_activation_mode": "mandatory_auto",
    "on_play_mode": "noop",
    "on_enter_mode": "auto",
    "on_activate_mode": "auto",
    "seals_level_size": 3,
    "seals_faith_per_level": 4,
    "seals_strength_per_level": 4,
    "triggered_effects": [
        {
            "trigger": {"event": "on_enter_field", "frequency": "each_turn"},
            "target": {
                "type": "cards_controlled_by_owner",
                "zone": "field",
                "owner": "me",
                "card_filter": {"name_contains": "__no_target__"},
                "target_policy": "optional_resolve",
                "selection_mode": "prompt",
                "cancel_behavior": "abort_step",
            },
            "effect": {"action": "add_seal_counter", "amount": 2},
        }
    ],
    "on_play_actions": [],
}

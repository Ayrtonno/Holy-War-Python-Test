from __future__ import annotations

CARD_NAME = """Spirito dei Sepolti"""

SCRIPT = {
    "default_selection_mode": "prompt",
    "default_cancel_behavior": "abort_step",
    "default_target_policy": "optional_resolve",
    "default_placement_policy": "prompt_slot_required",
    "default_activation_mode": "mandatory_auto",
    "on_play_mode": "noop",
    "on_enter_mode": "auto",
    "on_activate_mode": "auto",
    "triggered_effects": [
        {
            "trigger": {"event": "on_this_card_leaves_field", "frequency": "each_turn"},
            "target": {
                "type": "all_saints_on_field",
                "card_filter": {"exclude_event_card": True},
                "target_policy": "optional_resolve",
                "selection_mode": "prompt",
                "cancel_behavior": "abort_step",
            },
            "effect": {"action": "increase_faith", "amount": 1},
        },
        {
            "trigger": {"event": "on_this_card_leaves_field", "frequency": "each_turn"},
            "target": {
                "type": "all_saints_on_field",
                "card_filter": {"exclude_event_card": True},
                "target_policy": "optional_resolve",
                "selection_mode": "prompt",
                "cancel_behavior": "abort_step",
            },
            "effect": {"action": "increase_strength", "amount": 2},
        }
    ],
    "on_play_actions": [],
}

from __future__ import annotations

CARD_NAME = """Volere di Ph"""

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
            "trigger": {
                "event": "on_card_drawn",
                "frequency": "each_time",
                "condition": {"event_card_owner": "me"},
            },
            "target": {"type": "source_card"},
                "target_policy": "optional_resolve",
                "selection_mode": "prompt",
                "cancel_behavior": "abort_step",
            "effect": {"action": "inflict_sin", "amount": 1, "target_player": "me"},
        },
        {
            "trigger": {
                "event": "on_card_drawn",
                "frequency": "each_time",
                "condition": {"event_card_owner": "opponent"},
            },
            "target": {"type": "source_card"},
                "target_policy": "optional_resolve",
                "selection_mode": "prompt",
                "cancel_behavior": "abort_step",
            "effect": {"action": "inflict_sin", "amount": 1, "target_player": "opponent"},
        },
        {
            "trigger": {
                "event": "on_card_excommunicated",
                "frequency": "each_time",
            },
            "target": {"type": "source_card"},
                "target_policy": "optional_resolve",
                "selection_mode": "prompt",
                "cancel_behavior": "abort_step",
            "effect": {"action": "remove_sin", "amount": 1, "target_player": "me"},
        },
    ],
    "on_play_actions": [],
}

from __future__ import annotations

CARD_NAME = "Sigillo di Yin e Yang"

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
    "triggered_effects": [
        {
            "trigger": {
                "event": "on_sin_inflicted",
                "frequency": "each_time",
                "condition": {
                    "all_of": [
                        {"event_card_owner": "me"},
                        {"payload_target_player": "opponent"},
                    ]
                },
            },
            "target": {"type": "source_card"},
            "effect": {
                "action": "remove_sin_equal_to_stored_value",
                "target_player": "me",
                "target_policy": "optional_resolve",
                "selection_mode": "prompt",
                "cancel_behavior": "abort_step",
            },
        }
    ],
    "on_play_actions": [],
}

from __future__ import annotations

CARD_NAME = "Albero di Pietra"

SCRIPT = {
    "default_selection_mode": "prompt",
    "default_cancel_behavior": "abort_step",
    "default_target_policy": "optional_resolve",
    "default_placement_policy": "prompt_slot_required",
    "default_activation_mode": "mandatory_auto",
    "on_play_mode": "scripted",
    "on_enter_mode": "auto",
    "on_activate_mode": "auto",
    "triggered_effects": [
        {
            "trigger": {
                "event": "on_this_card_destroyed",
                "condition": {
                    "payload_reason_in": ["battle"],
                },
            },
            "target": {
                "type": "source_card",
                "target_policy": "optional_resolve",
                "selection_mode": "prompt",
                "cancel_behavior": "abort_step",
            },
            "effect": {
                "action": "optional_recover_matching_then_shuffle",
                "target_player": "me",
                "from_zone": "graveyard",
                "to_zone": "relicario",
                "card_name": "Pietra",
                "shuffle_after": True,
                "to_zone_if": "excommunicated",
            },
        },
    ],
    "on_play_actions": [],
}

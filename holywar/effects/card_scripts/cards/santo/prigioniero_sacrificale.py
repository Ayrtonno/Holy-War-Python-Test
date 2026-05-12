from __future__ import annotations

CARD_NAME = "Prigioniero Sacrificale"

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
                "event": "on_saint_defeated_or_destroyed",
                "frequency": "each_turn",
                "condition": {
                    "all_of": [
                        {"event_card_name_is": "Prigioniero Sacrificale"},
                        {"event_card_owner": "me"},
                    ]
                },
            },
            "target": {"type": "event_card"},
                "target_policy": "optional_resolve",
                "selection_mode": "prompt",
                "cancel_behavior": "abort_step",
            "effect": {"action": "excommunicate_card_no_sin"},
        },
        {
            "trigger": {
                "event": "on_card_excommunicated",
                "frequency": "each_time",
                "condition": {
                    "all_of": [
                        {"event_card_name_is": "Prigioniero Sacrificale"},
                        {"event_card_owner": "me"},
                    ]
                },
            },
            "target": {"type": "source_card"},
            "effect": {
                "action": "choose_up_to_n_from_hand_to_relicario_then_draw_same",
                "amount": 3,
                "target_player": "me",
                "target_policy": "optional_resolve",
                "selection_mode": "prompt",
                "cancel_behavior": "abort_step",
            },
        },
    ],
    "on_play_actions": [],
}

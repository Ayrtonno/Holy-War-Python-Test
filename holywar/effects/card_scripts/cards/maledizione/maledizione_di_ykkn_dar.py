from __future__ import annotations

CARD_NAME = 'Maledizione di Ykknødar'

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
    "triggered_effects": [],
    "on_play_actions": [
        {
            "activation_mode": "mandatory_auto",
            "effect": {
                "action": "process_deck_edges_by_type",
                "top_count": 5,
                "bottom_count": 5,
                "unique_edges_only": True,
                "saint_token_to_zone": "excommunicated",
                "blessing_curse_to_zone": "graveyard",
                "artifact_to_zone": "artifacts",
                "building_to_zone": "building",
                "fallback_to_zone": "graveyard",
                "replace_occupied_artifact": True,
                "replace_occupied_building": True,
            }
        },
        { "activation_mode": "mandatory_auto","effect": {"action": "move_source_to_zone", "to_zone": "excommunicated"}},
    ],
}

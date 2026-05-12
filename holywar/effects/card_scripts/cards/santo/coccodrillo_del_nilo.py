from __future__ import annotations

CARD_NAME = """Coccodrillo del Nilo"""

SCRIPT = {
    "default_selection_mode": "prompt",
    "default_cancel_behavior": "abort_step",
    "default_target_policy": "optional_resolve",
    "default_placement_policy": "prompt_slot_required",
    "default_activation_mode": "mandatory_auto",
    "on_play_mode": "noop",
    "on_enter_mode": "auto",
    "on_activate_mode": "auto",
    "protection_rules": [
        {
            "event": "target_by_effect",
            "source_owner": "enemy",
            "target_owner": "friendly",
            "source_card_types": ["maledizione"],
            "target_card_types": ["santo", "token"],
            "target_name_contains": "Coccodrillo del Nilo",
        },
        {
            "event": "destroy_by_effect",
            "source_owner": "enemy",
            "target_owner": "friendly",
            "source_card_types": ["maledizione"],
            "target_card_types": ["santo", "token"],
            "target_name_contains": "Coccodrillo del Nilo",
        },
    ],
    "triggered_effects": [],
    "on_play_actions": [],
}

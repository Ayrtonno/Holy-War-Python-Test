from __future__ import annotations

CARD_NAME = """Unut"""

SCRIPT = {
    "default_selection_mode": "prompt",
    "default_cancel_behavior": "abort_step",
    "default_target_policy": "optional_resolve",
    "default_placement_policy": "prompt_slot_required",
    "default_activation_mode": "mandatory_auto",
    "on_play_mode": "noop",
    "on_enter_mode": "auto",
    "on_activate_mode": "auto",
    "immune_to_actions": ["excommunicate_card", "excommunicate_card_no_sin"],
    "triggered_effects": [],
    "on_play_actions": [],
}

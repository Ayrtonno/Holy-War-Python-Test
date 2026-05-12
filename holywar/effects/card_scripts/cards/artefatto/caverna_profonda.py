from __future__ import annotations

CARD_NAME = """Caverna Profonda"""

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
                "event": "on_card_sent_to_graveyard",
                "frequency": "each_time",
                "condition": {
                    "payload_from_zone_in": ["attack", "defense", "artifact", "building", "field"],
                },
            },
            "target": {
                "type": "event_card",
                "card_filter": {"name_contains": "Pietra"},
                "target_policy": "optional_resolve",
                "selection_mode": "prompt",
                "cancel_behavior": "abort_step",
            },
            "effect": {"action": "move_to_relicario"},
        }
    ],
    "on_play_actions": [],
}

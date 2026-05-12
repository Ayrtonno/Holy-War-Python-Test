from __future__ import annotations

CARD_NAME = "Altare delle Otto Reliquie"

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
            "trigger": {"event": "on_card_drawn", "frequency": "each_time", "condition": {"event_card_owner": "me"}},
            "target": {"type": "cards_controlled_by_owner", "zone": "field", "owner": "me", "card_filter": {"name_contains": "ba xian", "card_type_in": ["santo", "token"]}},
                "target_policy": "optional_resolve",
                "selection_mode": "prompt",
                "cancel_behavior": "abort_step",
            "effect": {"action": "increase_faith", "amount": 1},
        },
        {
            "trigger": {"event": "on_card_drawn", "frequency": "each_time", "condition": {"event_card_owner": "me"}},
            "target": {"type": "cards_controlled_by_owner", "zone": "field", "owner": "me", "card_filter": {"name_contains": "ba xian", "card_type_in": ["santo", "token"]}},
                "target_policy": "optional_resolve",
                "selection_mode": "prompt",
                "cancel_behavior": "abort_step",
            "effect": {"action": "increase_strength", "amount": 1},
        },
    ],
    "on_play_actions": [],
}

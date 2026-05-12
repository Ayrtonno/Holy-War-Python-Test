from __future__ import annotations

CARD_NAME = """Gub-ner Antico"""

SCRIPT = {
    "default_selection_mode": "prompt",
    "default_cancel_behavior": "abort_step",
    "default_target_policy": "optional_resolve",
    "default_placement_policy": "prompt_slot_required",
    "default_activation_mode": "mandatory_auto",
    "on_play_mode": "noop",
    "on_enter_mode": "scripted",
    "on_activate_mode": "auto",
    "triggered_effects": [
        {
            "trigger": {"event": "on_saint_defeated_in_battle", "frequency": "each_time"},
            "condition": {"event_card_name_is": "Token Gub-ner"},
            "target": {
                "type": "cards_controlled_by_owner",
                "zone": "excommunicated",
                "owner": "any",
                "target_policy": "optional_resolve",
                "selection_mode": "prompt",
                "cancel_behavior": "abort_step",
            },
            "effect": {"action": "choose_targets", "min_targets": 0, "max_targets": 1},
        },
        {
            "trigger": {"event": "on_saint_defeated_in_battle", "frequency": "each_time"},
            "condition": {"event_card_name_is": "Token Gub-ner"},
            "target": {
                "type": "selected_target",
                "zone": "excommunicated",
                "owner": "any",
                "min_targets": 0,
                "max_targets": 1,
                "target_policy": "optional_resolve",
                "selection_mode": "prompt",
                "cancel_behavior": "abort_step",
            },
            "effect": {"action": "move_to_relicario"},
        },
        {
            "trigger": {"event": "on_saint_defeated_in_battle", "frequency": "each_time"},
            "condition": {"event_card_name_is": "Token Gub-ner"},
            "target": {
                "type": "selected_target",
                "zone": "deck",
                "owner": "any",
                "min_targets": 0,
                "max_targets": 1,
                "target_policy": "optional_resolve",
                "selection_mode": "prompt",
                "cancel_behavior": "abort_step",
            },
            "effect": {"action": "shuffle_target_owner_decks"},
        },
    ],
    "on_play_actions": [],
    "on_enter_actions": [
        {
            "activation_mode": "mandatory_auto",
            "target": {"type": "empty_saint_slots_controlled_by_owner", "owner": "me"},
                "selection_mode": "prompt",
                "cancel_behavior": "abort_step",
                "target_policy": "required_to_resolve",
                "selection_mode": "prompt",
                "cancel_behavior": "abort_step",
            "effect": {"action": "choose_targets", "min_targets": 1, "max_targets": 1},
        },
        {
            "activation_mode": "mandatory_auto",
            "target": {"type": "source_card"},
            "effect": {
                "action": "summon_generated_token",
                "placement_policy": "prompt_slot_required",
                "card_name": "Token Gub-ner",
                "owner": "me",
                "position": "selected_target_slot",
                "target_policy": "optional_resolve",
                "selection_mode": "prompt",
                "cancel_behavior": "abort_step",
            },
        },
    ],
}

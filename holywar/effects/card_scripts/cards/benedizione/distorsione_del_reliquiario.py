from __future__ import annotations

CARD_NAME = "Distorsione del Reliquiario"

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
                "action": "move_all_from_zone_to_zone",
                "from_zone": "excommunicated",
                "to_zone": "relicario",
                "target_player": "me",
                "shuffle_after": True,
            }
        },
        {
            "activation_mode": "mandatory_auto",
            "effect": {
                "action": "move_all_from_zone_to_zone",
                "from_zone": "excommunicated",
                "to_zone": "relicario",
                "target_player": "opponent",
                "shuffle_after": True,
            }
        },
        { "activation_mode": "mandatory_auto","effect": {"action": "draw_cards", "amount": 2, "target_player": "me"}},
        { "activation_mode": "mandatory_auto","effect": {"action": "draw_cards", "amount": 2, "target_player": "opponent"}},
    ],
}

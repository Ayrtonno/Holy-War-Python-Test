from __future__ import annotations

CARD_NAME = "Resurrezione del Sacerdote"

SCRIPT = {
    "on_play_mode": "scripted",
    "on_enter_mode": "auto",
    "on_activate_mode": "auto",
    "play_targeting": "none",
    "play_requirements": {"my_attack_count_lte": 0},
    "triggered_effects": [],
    "on_play_actions": [
        {
            "target": {"type": "source_card"},
            "effect": {"action": "draw_cards", "amount": 5, "target_player": "me"},
        },
        {
            "target": {"type": "source_card"},
            "effect": {"action": "set_no_attacks_this_turn"},
        },
    ],
}

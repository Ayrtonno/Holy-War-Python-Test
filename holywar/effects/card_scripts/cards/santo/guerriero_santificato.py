from __future__ import annotations

CARD_NAME = """Guerriero Santificato"""

SCRIPT = {
    "on_play_mode": "scripted",
    "on_enter_mode": "auto",
    "on_activate_mode": "scripted",
    "activate_once_per_turn": True,
    "activate_targeting": "guided",
    "can_attack_multiple_targets_in_attack_per_turn": True,
    "triggered_effects": [],
    "on_play_actions": [
        {"effect": {"action": "draw_cards", "amount": 0, "target_player": "me"}},
    ],
    "on_activate_actions": [
        {
            "target": {
                "type": "selected_target",
                "zone": "hand",
                "owner": "me",
                "min_targets": 1,
                "max_targets": 1,
            },
            "effect": {"action": "send_to_graveyard"},
        },
        {
            "target": {"type": "source_card"},
            "effect": {"action": "grant_extra_attack_this_turn"},
        },
    ],
}

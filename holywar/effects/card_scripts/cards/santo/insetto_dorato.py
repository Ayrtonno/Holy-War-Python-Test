from __future__ import annotations

CARD_NAME = """Insetto Dorato"""

SCRIPT = {
    "on_play_mode": "scripted",
    "on_enter_mode": "auto",
    "on_activate_mode": "auto",
    "can_attack_multiple_targets_in_attack_per_turn": True,
    "triggered_effects": [
        {
            "trigger": {"event": "on_this_card_deals_damage", "frequency": "each_time"},
            "target": {"type": "source_card"},
            "effect": {"action": "increase_strength", "amount": 1},
        }
    ],
    "on_play_actions": [],
}

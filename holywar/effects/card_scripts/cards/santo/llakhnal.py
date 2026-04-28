from __future__ import annotations

CARD_NAME = """Llakhnal"""

SCRIPT = {
    "on_play_mode": "noop",
    "on_enter_mode": "auto",
    "on_activate_mode": "auto",
    "attack_targeting": "untargetable",
    "triggered_effects": [
        {
            "trigger": {"event": "on_turn_start", "frequency": "each_time"},
            "target": {"type": "source_card"},
            "effect": {"action": "destroy_card"},
        },
    ],
    "on_play_actions": [],
}


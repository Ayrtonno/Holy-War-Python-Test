from __future__ import annotations

CARD_NAME = """Av'drna"""

SCRIPT = {
    "on_play_mode": "scripted",
    "on_enter_mode": "auto",
    "on_activate_mode": "auto",
    "triggered_effects": [
        {
            "trigger": {"event": "on_opponent_draws", "frequency": "each_turn"},
            "target": {"type": "cards_controlled_by_owner", "zone": "field", "owner": "me"},
            "effect": {"action": "av_drna_on_opponent_draw"}
        }
    ],
    "on_play_actions": [],
}


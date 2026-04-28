from __future__ import annotations

CARD_NAME = "Esondazione del Nilo"

SCRIPT = {
    "on_play_mode": "scripted",
    "on_enter_mode": "auto",
    "on_activate_mode": "auto",
    "triggered_effects": [
        {
            "trigger": {"event": "on_draw_phase_start", "frequency": "each_turn"},
            "target": {"type": "source_card"},
            "effect": {"action": "draw_cards", "amount": 1, "target_player": "me"},
        }
    ],
    "on_play_actions": [],
}

from __future__ import annotations

CARD_NAME = "Furia di Camazotz"

SCRIPT = {
    "on_play_mode": "scripted",
    "on_enter_mode": "auto",
    "on_activate_mode": "auto",
    "triggered_effects": [],
    "on_play_actions": [
        {
            "target": {"type": "source_card"},
            "effect": {
                "action": "choose_draw_amount_with_self_sin_cost",
                "amount": 15,
                "target_player": "me",
                "choice_title": "Furia di Camazotz",
                "choice_prompt": "Quante carte vuoi pescare? (15 Peccato per carta pescata)",
            },
        },
    ],
}

from __future__ import annotations

CARD_NAME = """Huginn"""

SCRIPT = {
    "on_play_mode": "noop",
    "play_targeting": "none",
    "on_enter_mode": "scripted",
    "on_activate_mode": "auto",
    "triggered_effects": [],
    "on_play_actions": [],
    "on_enter_actions": [
        {
            "condition": {"controller_has_saint_with_name": "Odino"},
            "effect": {"action": "optional_draw_from_top_n_then_shuffle", "amount": 3, "target_player": "me"},
        },
    ],
}

from __future__ import annotations

CARD_NAME = "Sacrificio: Dolore"

SCRIPT = {
    "on_play_mode": "scripted",
    "on_enter_mode": "auto",
    "on_activate_mode": "auto",
    "triggered_effects": [
        {
            "trigger": {"event": "on_card_excommunicated", "frequency": "each_time"},
            "condition": {"event_card_owner": "me"},
            "target": {"type": "source_card"},
            "effect": {"action": "inflict_sin", "amount": 3, "target_player": "opponent"},
        },
    ],
    "on_play_actions": [],
}

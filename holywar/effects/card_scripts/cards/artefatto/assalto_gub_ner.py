from __future__ import annotations

CARD_NAME = "Assalto Gub-ner"

SCRIPT = {
    "on_play_mode": "scripted",
    "on_enter_mode": "auto",
    "on_activate_mode": "scripted",
    "activate_once_per_turn": True,
    "activate_targeting": "none",
    "triggered_effects": [],
    "on_play_actions": [],
    "on_activate_actions": [
        {
            "target": {"type": "source_card"},
            "effect": {"action": "summon_generated_token", "card_name": "Token Gub-ner", "owner": "me"},
        }
    ],
}

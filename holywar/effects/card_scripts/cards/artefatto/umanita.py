from __future__ import annotations

CARD_NAME = "Umanità"

SCRIPT = {
    "on_play_mode": "scripted",
    "on_enter_mode": "auto",
    "on_activate_mode": "auto",
    "play_targeting": "none",
    "protection_rules": [
        {
            "event": "sin_on_death",
            "source_owner": "any",
            "target_owner": "friendly",
            "target_card_types": ["santo", "token"],
            "target_equipped_by_card_types": ["benedizione"],
        }
    ],
    "triggered_effects": [],
    "on_play_actions": [],
}

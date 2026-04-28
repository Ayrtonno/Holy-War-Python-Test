from __future__ import annotations

CARD_NAME = """Terra"""

SCRIPT = {
    "on_play_mode": "scripted",
    "on_enter_mode": "auto",
    "on_activate_mode": "auto",
    "protection_rules": [
        {
            "event": "destroy_by_effect",
            "source_owner": "enemy",
            "target_owner": "friendly",
            "source_card_types": ["artefatto"],
            "target_card_types": ["santo", "token"],
        }
    ],
    "triggered_effects": [],
    "on_play_actions": [],
}

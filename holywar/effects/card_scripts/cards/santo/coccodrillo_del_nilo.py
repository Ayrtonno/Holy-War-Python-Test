from __future__ import annotations

CARD_NAME = """Coccodrillo del Nilo"""

SCRIPT = {
    "on_play_mode": "noop",
    "on_enter_mode": "auto",
    "on_activate_mode": "auto",
    "protection_rules": [
        {
            "event": "target_by_effect",
            "source_owner": "enemy",
            "target_owner": "friendly",
            "source_card_types": ["maledizione"],
            "target_card_types": ["santo", "token"],
            "target_name_contains": "Coccodrillo del Nilo",
        },
        {
            "event": "destroy_by_effect",
            "source_owner": "enemy",
            "target_owner": "friendly",
            "source_card_types": ["maledizione"],
            "target_card_types": ["santo", "token"],
            "target_name_contains": "Coccodrillo del Nilo",
        },
    ],
    "triggered_effects": [],
    "on_play_actions": [],
}

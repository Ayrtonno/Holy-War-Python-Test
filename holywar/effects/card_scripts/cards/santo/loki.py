from __future__ import annotations

CARD_NAME = """Loki"""

SCRIPT = {
    "on_play_mode": "noop",
    "on_enter_mode": "auto",
    "on_activate_mode": "scripted",
    "play_targeting": "none",
    "activate_targeting": "manual",
    "triggered_effects": [],
    "on_play_actions": [],
    "on_activate_actions": [
        {
            "condition": {"selected_target_in": ["Fenrir", "Jormungandr"]},
            "target": {"type": "source_card"},
            "effect": {"action": "remove_from_board_no_sin"},
        },
        {
            "condition": {"selected_target_in": ["Fenrir", "Jormungandr"]},
            "target": {"type": "source_card"},
            "effect": {"action": "summon_card_from_hand"},
        },
    ],
}


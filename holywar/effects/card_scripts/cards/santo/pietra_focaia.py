from __future__ import annotations

CARD_NAME = "Pietra Focaia"

SCRIPT = {
    "on_play_mode": "scripted",
    "on_enter_mode": "auto",
    "on_activate_mode": "auto",
    "triggered_effects": [
        {
            "trigger": {
                "event": "on_this_card_attacks",
                "condition": {"payload_target_slot_is_set": True},
            },
            "target": {
                "type": "source_card",
            },
            "effect": {
                "action": "choose_artifact_from_relicario_then_shuffle",
                "target_player": "me",
            },
        },
    ],
    "on_play_actions": [],
}

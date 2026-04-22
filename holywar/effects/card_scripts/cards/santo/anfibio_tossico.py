from __future__ import annotations

CARD_NAME = """Anfibio Tossico"""

SCRIPT = {
    "on_play_mode": "scripted",
    "on_enter_mode": "auto",
    "on_activate_mode": "auto",
    "triggered_effects": [
        {
            "trigger": {"event": "on_this_card_deals_damage", "frequency": "each_turn"},
            "target": {
                "type": "payload_target_card",
                "card_filter": {"card_type_in": ["santo", "token"]},
            },
            "effect": {"action": "equip_card"},
        },
        {
            "trigger": {"event": "on_opponent_turn_end", "frequency": "each_turn"},
            "target": {"type": "source_card"},
            "effect": {"action": "destroy_equipped_target_and_excommunicate_source"},
        },
    ],
    "on_play_actions": [],
}

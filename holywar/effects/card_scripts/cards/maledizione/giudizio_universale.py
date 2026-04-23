from __future__ import annotations

CARD_NAME = 'Giudizio Universale'

SCRIPT = {
    "on_play_mode": "scripted",
    "on_enter_mode": "auto",
    "on_activate_mode": "auto",
    "play_targeting": "none",
    "triggered_effects": [],
    "on_play_actions": [
        {
            "target": {
                "type": "cards_controlled_by_owner",
                "zone": "graveyard",
                "owner": "any",
            },
            "effect": {"action": "move_to_relicario"},
        },
        {
            "target": {"type": "source_card"},
            "effect": {"action": "shuffle_target_owner_decks"},
        },
    ],
}

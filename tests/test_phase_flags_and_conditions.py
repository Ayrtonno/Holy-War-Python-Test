from __future__ import annotations

from holywar.core.engine import GameEngine
from holywar.data.models import CardDefinition
from holywar.effects.runtime import runtime_cards


def _advance_to_active_phase(engine: GameEngine) -> None:
    engine.start_turn()
    engine.end_turn()
    engine.start_turn()
    engine.end_turn()
    assert engine.state.phase == "active"
    engine.start_turn()


def _force_card_in_hand(engine: GameEngine, player_idx: int, name: str) -> int:
    player = engine.state.players[player_idx]
    for i, uid in enumerate(player.hand):
        if engine.state.instances[uid].definition.name == name:
            return i
    for i, uid in enumerate(player.deck):
        if engine.state.instances[uid].definition.name == name:
            found = player.deck.pop(i)
            player.hand.append(found)
            return len(player.hand) - 1
    raise AssertionError(f"Carta non trovata: {name}")


def test_battle_phase_events_emit_on_first_attack_and_end_turn() -> None:
    cards = [
        CardDefinition("A1", "Santo", "2", 5, 2, "", "NEU-1"),
        CardDefinition("B1", "Santo", "2", 5, 2, "", "NEU-1"),
    ]
    engine = GameEngine.create_new(cards, "P1", "P2", "NEU-1", "NEU-1", seed=301)
    _advance_to_active_phase(engine)
    while engine.state.active_player != 0:
        engine.end_turn()
        engine.start_turn()

    events: list[str] = []
    engine.rules_api(0).subscribe("on_battle_phase_start", lambda ctx: events.append(ctx.event))
    engine.rules_api(0).subscribe("on_battle_phase_end", lambda ctx: events.append(ctx.event))

    i_a = _force_card_in_hand(engine, 0, "A1")
    assert engine.play_card(0, i_a, "a1").ok
    engine.end_turn()
    engine.start_turn()
    i_b = _force_card_in_hand(engine, 1, "B1")
    assert engine.play_card(1, i_b, "a1").ok
    engine.end_turn()
    engine.start_turn()

    assert engine.attack(0, 0, 0).ok
    assert "on_battle_phase_start" in events
    engine.end_turn()
    assert "on_battle_phase_end" in events


def test_condition_tree_and_action_alias_work_for_runtime_trigger() -> None:
    runtime_cards.register_script_from_dict(
        "Aura Condizioni",
        {
            "on_play_mode": "auto",
            "on_enter_mode": "auto",
            "on_activate_mode": "auto",
            "triggered_effects": [
                {
                        "trigger": {
                            "event": "on_draw_phase_end",
                            "condition": {
                                "all_of": [
                                    {"turn_scope": "my"},
                                    {"opponent_saints_lte": 3},
                                ]
                        },
                    },
                    "target": {"type": "cards_controlled_by_owner", "zone": "field", "owner": "me"},
                    "effect": {"action": "gain_inspiration", "amount": 1},
                }
            ],
        },
    )
    cards = [
        CardDefinition("Aura Condizioni", "Artefatto", "2", 0, None, "", "NEU-1"),
        CardDefinition("Fill", "Santo", "2", 2, 1, "", "NEU-1"),
    ]
    engine = GameEngine.create_new(cards, "P1", "P2", "NEU-1", "NEU-1", seed=302)
    _advance_to_active_phase(engine)
    while engine.state.active_player != 0:
        engine.end_turn()
        engine.start_turn()
    i_aura = _force_card_in_hand(engine, 0, "Aura Condizioni")
    assert engine.play_card(0, i_aura, None).ok
    engine.end_turn()
    engine.start_turn()
    engine.end_turn()
    engine.start_turn()
    assert engine.state.active_player == 0
    # 10 base inspiration + 1 from trigger alias "gain_inspiration"
    assert engine.state.players[0].inspiration >= 11

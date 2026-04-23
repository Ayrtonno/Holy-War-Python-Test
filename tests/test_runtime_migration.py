from __future__ import annotations

import json
from pathlib import Path

from holywar.core.engine import GameEngine
from holywar.core.state import GameState
from holywar.data.models import CardDefinition
from holywar.effects.runtime import RuntimeCardManager, runtime_cards


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


def test_all_cards_are_runtime_migrated_at_engine_creation() -> None:
    runtime_cards.clear_for_tests()
    cards = [
        CardDefinition("A", "Santo", "2", 1, 1, "", "NEU-1"),
        CardDefinition("B", "Benedizione", "1", None, None, "", "NEU-1"),
        CardDefinition("C", "Artefatto", "1", 1, None, "", "NEU-1"),
    ]
    engine = GameEngine.create_new(cards, "P1", "P2", "NEU-1", "NEU-1", seed=41)
    names = {_n.definition.name for _n in engine.state.instances.values()}
    assert runtime_cards.migrated_count() >= len(names)
    for name in names:
        assert runtime_cards.is_migrated(name)


def test_runtime_bootstrap_covers_entire_cards_catalog() -> None:
    manager = RuntimeCardManager()
    cards_path = Path("holywar/data/cards.json")
    rows = json.loads(cards_path.read_text(encoding="utf-8"))
    names = {str(r.get("name", "")).strip() for r in rows if isinstance(r, dict) and str(r.get("name", "")).strip()}
    assert names
    for name in names:
        assert manager.is_migrated(name)


def test_declarative_trigger_foresta_sacra_like_structure() -> None:
    runtime_cards.clear_for_tests()
    runtime_cards.register_script_from_dict(
        "Aura Albero Test",
        {
            "on_play_mode": "legacy",
            "on_enter_mode": "legacy",
            "on_activate_mode": "legacy",
            "triggered_effects": [
                {
                    "trigger": {"event": "on_my_turn_start", "frequency": "each_turn"},
                    "target": {
                        "type": "cards_controlled_by_owner",
                        "card_filter": {"name_contains": "Albero"},
                        "zone": "field",
                        "owner": "me",
                    },
                    "effect": {"action": "increase_faith", "amount": 2, "duration": "until_source_leaves"},
                }
            ],
        },
    )

    cards = [
        CardDefinition("Aura Albero Test", "Artefatto", "2", 0, None, "", "NEU-1"),
        CardDefinition("Albero Sacro", "Santo", "2", 5, 1, "", "NEU-1"),
        CardDefinition("Thor", "Santo", "2", 5, 1, "", "NEU-1"),
    ]
    engine = GameEngine.create_new(cards, "P1", "P2", "NEU-1", "NEU-1", seed=42)
    _advance_to_active_phase(engine)
    while engine.state.active_player != 0:
        engine.end_turn()
        engine.start_turn()

    i_aura = _force_card_in_hand(engine, 0, "Aura Albero Test")
    assert engine.play_card(0, i_aura, None).ok
    i_tree = _force_card_in_hand(engine, 0, "Albero Sacro")
    assert engine.play_card(0, i_tree, "a1").ok
    i_other = _force_card_in_hand(engine, 0, "Thor")
    assert engine.play_card(0, i_other, "a2").ok

    p0 = engine.state.players[0]
    tree_uid = p0.attack[0]
    thor_uid = p0.attack[1]
    assert tree_uid and thor_uid
    tree_before = engine.state.instances[tree_uid].current_faith
    thor_before = engine.state.instances[thor_uid].current_faith

    engine.end_turn()
    engine.start_turn()
    engine.end_turn()
    engine.start_turn()

    assert engine.state.instances[tree_uid].current_faith == (tree_before or 0) + 2
    assert engine.state.instances[thor_uid].current_faith == thor_before


def test_fuoco_is_declarative_trigger_and_applies_end_turn_damage() -> None:
    runtime_cards.clear_for_tests()
    runtime_cards._bootstrap_from_cards_json()  # type: ignore[attr-defined]
    runtime_cards.register_script_from_dict(
        "Fuoco",
        {
            "on_play_mode": "auto",
            "on_enter_mode": "auto",
            "on_activate_mode": "auto",
            "triggered_effects": [
                {
                    "trigger": {"event": "on_turn_end", "frequency": "each_turn"},
                    "target": {
                        "type": "all_saints_on_field",
                        "card_filter": {"card_type_in": ["santo", "token"], "crosses_gte": 4},
                    },
                    "effect": {
                        "action": "decrease_faith",
                        "amount": 2,
                        "amount_multiplier_card_name": "Fuoco",
                    },
                }
            ],
        },
    )

    cards = [
        CardDefinition("Fuoco", "Artefatto", "2", 1, None, "", "NEU-1"),
        CardDefinition("Big", "Santo", "4", 1, 1, "", "NEU-1"),
        CardDefinition("Small", "Santo", "3", 1, 1, "", "NEU-1"),
    ]
    engine = GameEngine.create_new(cards, "P1", "P2", "NEU-1", "NEU-1", seed=43)
    _advance_to_active_phase(engine)
    while engine.state.active_player != 0:
        engine.end_turn()
        engine.start_turn()

    i_fuoco = _force_card_in_hand(engine, 0, "Fuoco")
    assert engine.play_card(0, i_fuoco, None).ok
    i_big = _force_card_in_hand(engine, 0, "Big")
    assert engine.play_card(0, i_big, "a1").ok
    i_small = _force_card_in_hand(engine, 0, "Small")
    assert engine.play_card(0, i_small, "a2").ok
    p0 = engine.state.players[0]
    big_uid = p0.attack[0]
    small_uid = p0.attack[1]
    assert big_uid and small_uid
    big_before = engine.state.instances[big_uid].current_faith
    small_before = engine.state.instances[small_uid].current_faith

    engine.end_turn()
    assert engine.state.instances[big_uid].current_faith == max(0, (big_before or 0) - 2)
    assert engine.state.instances[small_uid].current_faith == small_before


def test_campana_counter_tick_is_runtime_declarative() -> None:
    runtime_cards.register_script_from_dict(
        "Campana",
        {
            "on_play_mode": "auto",
            "on_enter_mode": "auto",
            "on_activate_mode": "auto",
            "triggered_effects": [
                {
                    "trigger": {"event": "on_my_turn_start", "frequency": "each_turn"},
                    "target": {"type": "cards_controlled_by_owner", "zone": "field", "owner": "me"},
                    "effect": {"action": "campana_add_counter"},
                }
            ],
        },
    )
    cards = [
        CardDefinition("Campana", "Artefatto", "2", 1, None, "", "NEU-1"),
    ]
    engine = GameEngine.create_new(cards, "P1", "P2", "NEU-1", "NEU-1", seed=44)
    _advance_to_active_phase(engine)
    while engine.state.active_player != 0:
        engine.end_turn()
        engine.start_turn()
    i_campana = _force_card_in_hand(engine, 0, "Campana")
    assert engine.play_card(0, i_campana, None).ok
    a_uid = next(uid for uid in engine.state.players[0].artifacts if uid is not None)
    assert a_uid is not None
    engine.end_turn()
    engine.start_turn()
    engine.end_turn()
    engine.start_turn()
    tags = engine.state.instances[a_uid].blessed
    assert any(t.startswith("campana_counter:") for t in tags)


def test_runtime_triggers_are_rebound_when_engine_is_recreated_from_state() -> None:
    runtime_cards.clear_for_tests()
    runtime_cards._bootstrap_from_cards_json()  # type: ignore[attr-defined]
    runtime_cards.register_script_from_dict(
        "Fuoco",
        {
            "on_play_mode": "auto",
            "on_enter_mode": "auto",
            "on_activate_mode": "auto",
            "triggered_effects": [
                {
                    "trigger": {"event": "on_turn_end", "frequency": "each_turn"},
                    "target": {
                        "type": "all_saints_on_field",
                        "card_filter": {"card_type_in": ["santo", "token"], "crosses_gte": 4},
                    },
                    "effect": {"action": "decrease_faith", "amount": 2, "amount_multiplier_card_name": "Fuoco"},
                }
            ],
        },
    )
    cards = [
        CardDefinition("Fuoco", "Artefatto", "2", 1, None, "", "NEU-1"),
        CardDefinition("Big", "Santo", "4", 5, 1, "", "NEU-1"),
        CardDefinition("Filler", "Santo", "2", 1, 1, "", "NEU-1"),
    ]
    engine = GameEngine.create_new(cards, "P1", "P2", "NEU-1", "NEU-1", seed=45)
    _advance_to_active_phase(engine)
    while engine.state.active_player != 0:
        engine.end_turn()
        engine.start_turn()
    i_fuoco = _force_card_in_hand(engine, 0, "Fuoco")
    assert engine.play_card(0, i_fuoco, None).ok
    i_big = _force_card_in_hand(engine, 0, "Big")
    assert engine.play_card(0, i_big, "a1").ok
    big_uid = engine.state.players[0].attack[0]
    assert big_uid is not None
    before = engine.state.instances[big_uid].current_faith or 0

    restored_state = GameState.from_dict(engine.state.to_dict())
    restored_engine = GameEngine(restored_state, seed=45)
    restored_engine.end_turn()
    after = restored_engine.state.instances[big_uid].current_faith or 0
    assert after == max(0, before - 2)

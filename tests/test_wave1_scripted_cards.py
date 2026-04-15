from __future__ import annotations

from holywar.core.engine import GameEngine
from holywar.data.models import CardDefinition


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


def test_aria_adds_one_inspiration_on_own_turn() -> None:
    cards = [
        CardDefinition("Aria", "Artefatto", "1", 1, None, "", "NEU-1"),
        CardDefinition("Fill", "Santo", "1", 1, 1, "", "NEU-1"),
    ]
    engine = GameEngine.create_new(cards, "P1", "P2", "NEU-1", "NEU-1", seed=511)
    _advance_to_active_phase(engine)
    while engine.state.active_player != 0:
        engine.end_turn()
        engine.start_turn()
    i = _force_card_in_hand(engine, 0, "Aria")
    assert engine.play_card(0, i, None).ok
    engine.end_turn()
    engine.start_turn()
    engine.end_turn()
    engine.start_turn()
    assert engine.state.active_player == 0
    assert engine.state.players[0].inspiration == 11


def test_valhalla_adds_two_inspiration_on_own_turn() -> None:
    cards = [
        CardDefinition("Valhalla", "Edificio", "1", 1, None, "", "NEU-1"),
        CardDefinition("Fill", "Santo", "1", 1, 1, "", "NEU-1"),
    ]
    engine = GameEngine.create_new(cards, "P1", "P2", "NEU-1", "NEU-1", seed=512)
    _advance_to_active_phase(engine)
    while engine.state.active_player != 0:
        engine.end_turn()
        engine.start_turn()
    v = _force_card_in_hand(engine, 0, "Valhalla")
    assert engine.play_card(0, v, None).ok
    engine.end_turn()
    engine.start_turn()
    engine.end_turn()
    engine.start_turn()
    assert engine.state.players[0].inspiration == 12


def test_ruscello_sacro_adds_two_inspiration_on_own_turn() -> None:
    cards = [
        CardDefinition("Ruscello Sacro", "Edificio", "1", 1, None, "", "NEU-1"),
        CardDefinition("Fill", "Santo", "1", 1, 1, "", "NEU-1"),
    ]
    engine = GameEngine.create_new(cards, "P1", "P2", "NEU-1", "NEU-1", seed=516)
    _advance_to_active_phase(engine)
    while engine.state.active_player != 0:
        engine.end_turn()
        engine.start_turn()
    r = _force_card_in_hand(engine, 0, "Ruscello Sacro")
    assert engine.play_card(0, r, None).ok
    engine.end_turn()
    engine.start_turn()
    engine.end_turn()
    engine.start_turn()
    assert engine.state.players[0].inspiration == 12


def test_esondazione_del_nilo_draws_one_extra_card_on_draw_phase() -> None:
    cards = [
        CardDefinition("Esondazione del Nilo", "Artefatto", "1", 1, None, "", "NEU-1"),
        CardDefinition("Fill", "Santo", "1", 1, 1, "", "NEU-1"),
    ]
    engine = GameEngine.create_new(cards, "P1", "P2", "NEU-1", "NEU-1", seed=513)
    _advance_to_active_phase(engine)
    while engine.state.active_player != 0:
        engine.end_turn()
        engine.start_turn()
    e = _force_card_in_hand(engine, 0, "Esondazione del Nilo")
    assert engine.play_card(0, e, None).ok
    hand_before = len(engine.state.players[0].hand)
    engine.end_turn()
    engine.start_turn()
    engine.end_turn()
    engine.start_turn()
    hand_after = len(engine.state.players[0].hand)
    assert hand_after >= hand_before + 1


def test_chiesa_gives_plus_two_faith_on_each_own_draw() -> None:
    cards = [
        CardDefinition("Chiesa", "Edificio", "1", 1, None, "", "NEU-1"),
        CardDefinition("S", "Santo", "1", 3, 1, "", "NEU-1"),
        CardDefinition("F", "Santo", "1", 1, 1, "", "NEU-1"),
    ]
    engine = GameEngine.create_new(cards, "P1", "P2", "NEU-1", "NEU-1", seed=514)
    _advance_to_active_phase(engine)
    while engine.state.active_player != 0:
        engine.end_turn()
        engine.start_turn()
    c = _force_card_in_hand(engine, 0, "Chiesa")
    assert engine.play_card(0, c, None).ok
    s = _force_card_in_hand(engine, 0, "S")
    assert engine.play_card(0, s, "a1").ok
    uid = engine.state.players[0].attack[0]
    assert uid is not None
    before = engine.state.instances[uid].current_faith or 0
    engine.draw_cards(0, 1)
    after = engine.state.instances[uid].current_faith or 0
    assert after == before + 2


def test_frate_curatore_buffs_own_saints_when_opponent_draws() -> None:
    cards = [
        CardDefinition("Frate Curatore", "Santo", "1", 3, 1, "", "NEU-1"),
        CardDefinition("S", "Santo", "1", 3, 1, "", "NEU-1"),
        CardDefinition("F", "Santo", "1", 1, 1, "", "NEU-1"),
    ]
    engine = GameEngine.create_new(cards, "P1", "P2", "NEU-1", "NEU-1", seed=515)
    _advance_to_active_phase(engine)
    while engine.state.active_player != 0:
        engine.end_turn()
        engine.start_turn()
    f = _force_card_in_hand(engine, 0, "Frate Curatore")
    assert engine.play_card(0, f, "a1").ok
    s = _force_card_in_hand(engine, 0, "S")
    assert engine.play_card(0, s, "a2").ok
    uid = engine.state.players[0].attack[1]
    assert uid is not None
    before = engine.state.instances[uid].current_faith or 0
    engine.draw_cards(1, 1)
    after = engine.state.instances[uid].current_faith or 0
    assert after == before + 1

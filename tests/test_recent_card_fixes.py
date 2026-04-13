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


def test_cura_rapida_heals_all_own_saints() -> None:
    cards = [
        CardDefinition("S1", "Santo", "2", 5, 1, "", "NEU-1"),
        CardDefinition("S2", "Santo", "2", 5, 1, "", "NEU-1"),
        CardDefinition("Cura Rapida", "Benedizione", "1", None, None, "Conferisci +2 fede ai tuoi santi.", "NEU-1"),
    ]
    engine = GameEngine.create_new(cards, "P1", "P2", "NEU-1", "NEU-1", seed=1)
    _advance_to_active_phase(engine)
    while engine.state.active_player != 0:
        engine.end_turn()
        engine.start_turn()
    p1 = engine.state.players[0]
    i1 = _force_card_in_hand(engine, 0, "S1")
    assert engine.play_card(0, i1, "a1").ok
    i2 = _force_card_in_hand(engine, 0, "S2")
    assert engine.play_card(0, i2, "a2").ok
    uid1 = p1.attack[0]
    uid2 = p1.attack[1]
    assert uid1 and uid2
    engine.state.instances[uid1].current_faith = 2
    engine.state.instances[uid2].current_faith = 1
    q = _force_card_in_hand(engine, 0, "Cura Rapida")
    assert engine.play_card(0, q, None).ok
    assert engine.state.instances[uid1].current_faith == 4
    assert engine.state.instances[uid2].current_faith == 3


def test_ricerca_archeologica_uses_named_target() -> None:
    cards = [
        CardDefinition("A1", "Artefatto", "1", 1, None, "", "NEU-1"),
        CardDefinition("A2", "Artefatto", "1", 1, None, "", "NEU-1"),
        CardDefinition("Ricerca Archeologica", "Benedizione", "1", None, None, "Cerca un artefatto nel reliquiario.", "NEU-1"),
    ]
    engine = GameEngine.create_new(cards, "P1", "P2", "NEU-1", "NEU-1", seed=2)
    _advance_to_active_phase(engine)
    while engine.state.active_player != 0:
        engine.end_turn()
        engine.start_turn()
    q = _force_card_in_hand(engine, 0, "Ricerca Archeologica")
    out = engine.play_card(0, q, "A2")
    assert out.ok
    hand_names = [engine.state.instances[uid].definition.name for uid in engine.state.players[0].hand]
    assert "A2" in hand_names


def test_ya_ner_summons_token_at_turn_start() -> None:
    cards = [
        CardDefinition("Ya-ner", "Santo", "3", 5, 2, "", "PHD-1"),
        CardDefinition("Token Gub-ner", "Token", "1", 1, 0, "", "PHD-1"),
    ]
    engine = GameEngine.create_new(cards, "P1", "P2", "PHD-1", "PHD-1", seed=3)
    _advance_to_active_phase(engine)
    while engine.state.active_player != 0:
        engine.end_turn()
        engine.start_turn()
    idx = _force_card_in_hand(engine, 0, "Ya-ner")
    assert engine.play_card(0, idx, "a1").ok
    engine.end_turn()
    engine.start_turn()
    assert engine.state.active_player == 1
    engine.end_turn()
    engine.start_turn()
    p1 = engine.state.players[0]
    d = p1.defense[0]
    assert d is not None
    assert engine.state.instances[d].definition.name == "Token Gub-ner"


def test_ya_ner_battle_destruction_is_replaced_by_token() -> None:
    cards = [
        CardDefinition("Ya-ner", "Santo", "3", 5, 2, "", "PHD-1"),
        CardDefinition("Token Gub-ner", "Token", "1", 1, 0, "", "PHD-1"),
        CardDefinition("Killer", "Santo", "3", 6, 10, "", "ANI-1"),
    ]
    engine = GameEngine.create_new(cards, "P1", "P2", "PHD-1", "ANI-1", seed=5)
    _advance_to_active_phase(engine)
    while engine.state.active_player != 0:
        engine.end_turn()
        engine.start_turn()
    p1 = engine.state.players[0]
    p2 = engine.state.players[1]

    y_idx = _force_card_in_hand(engine, 0, "Ya-ner")
    assert engine.play_card(0, y_idx, "a1").ok
    # Move to P2 turn and back to trigger Ya-ner start-turn token summon.
    engine.end_turn()
    engine.start_turn()
    k_idx = _force_card_in_hand(engine, 1, "Killer")
    assert engine.play_card(1, k_idx, "a1").ok
    engine.end_turn()
    engine.start_turn()

    assert p1.attack[0] is not None and engine.state.instances[p1.attack[0]].definition.name == "Ya-ner"
    assert p1.defense[0] is not None and engine.state.instances[p1.defense[0]].definition.name == "Token Gub-ner"

    # Killer attacks Ya-ner lethally; token should be destroyed instead and Ya-ner restored.
    engine.end_turn()
    engine.start_turn()
    out = engine.attack(1, 0, 0)
    assert out.ok
    assert p1.attack[0] is not None
    assert engine.state.instances[p1.attack[0]].definition.name == "Ya-ner"
    assert engine.state.instances[p1.attack[0]].current_faith == engine.state.instances[p1.attack[0]].definition.faith
    assert p1.defense[0] is None


def test_pkad_nok_destroys_both_cards_in_combat() -> None:
    cards = [
        CardDefinition("Pkad-nok", "Santo", "3", 6, 3, "", "PHD-1"),
        CardDefinition("Enemy", "Santo", "3", 6, 3, "", "ANI-1"),
    ]
    engine = GameEngine.create_new(cards, "P1", "P2", "PHD-1", "ANI-1", seed=4)
    _advance_to_active_phase(engine)
    while engine.state.active_player != 0:
        engine.end_turn()
        engine.start_turn()
    i1 = _force_card_in_hand(engine, 0, "Pkad-nok")
    assert engine.play_card(0, i1, "a1").ok
    engine.end_turn()
    engine.start_turn()
    i2 = _force_card_in_hand(engine, 1, "Enemy")
    assert engine.play_card(1, i2, "a1").ok
    engine.end_turn()
    engine.start_turn()
    out = engine.attack(0, 0, 0)
    assert out.ok
    assert engine.state.players[0].attack[0] is None
    assert engine.state.players[1].attack[0] is None

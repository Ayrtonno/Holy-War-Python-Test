from __future__ import annotations

from holywar.core.engine import GameEngine
from holywar.data.models import CardDefinition


def _cards() -> list[CardDefinition]:
    return [
        CardDefinition("Guerriero", "Santo", "2", 5, 10, "", "Animismo"),
        CardDefinition("Difensore", "Santo", "2", 4, 2, "", "Animismo"),
        CardDefinition("Cura", "Benedizione", "1", None, None, "", "Neutre"),
        CardDefinition("Corruzione", "Maledizione", "1", None, None, "", "Neutre"),
    ]


def _advance_to_active_phase(engine: GameEngine) -> None:
    # P1 prep
    engine.start_turn()
    engine.end_turn()
    # P2 prep
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


def test_play_and_attack_generates_sin_on_death() -> None:
    engine = GameEngine.create_new(_cards(), "P1", "P2", "Animismo", "Animismo", seed=1)
    _advance_to_active_phase(engine)

    # Force controlled hand/deck setup.
    p1 = engine.state.players[0]
    p2 = engine.state.players[1]

    # Put a saint from p1 hand to attack.
    saint_idx = _force_card_in_hand(engine, 0, "Guerriero")
    assert engine.play_card(0, saint_idx, "a1").ok

    engine.end_turn()
    engine.start_turn()

    enemy_idx = _force_card_in_hand(engine, 1, "Difensore")
    assert engine.play_card(1, enemy_idx, "a1").ok

    engine.end_turn()
    engine.start_turn()
    res = engine.attack(0, 0, 0)
    assert res.ok
    assert p2.sin >= 4


def test_direct_attack_adds_sin() -> None:
    engine = GameEngine.create_new(_cards(), "P1", "P2", "Animismo", "Animismo", seed=2)
    _advance_to_active_phase(engine)
    p1 = engine.state.players[0]
    saint_idx = _force_card_in_hand(engine, 0, "Guerriero")
    assert engine.play_card(0, saint_idx, "a1").ok
    out = engine.attack(0, 0, None)
    assert out.ok
    assert engine.state.players[1].sin > 0


def test_invalid_play_on_occupied_slot_does_not_spend_inspiration() -> None:
    engine = GameEngine.create_new(_cards(), "P1", "P2", "Animismo", "Animismo", seed=3)
    _advance_to_active_phase(engine)
    p1 = engine.state.players[0]

    first_idx = _force_card_in_hand(engine, 0, "Guerriero")
    assert engine.play_card(0, first_idx, "a1").ok
    inspiration_after_first = p1.inspiration

    second_idx = _force_card_in_hand(engine, 0, "Guerriero")
    hand_len_before = len(p1.hand)
    out = engine.play_card(0, second_idx, "a1")

    assert not out.ok
    assert p1.inspiration == inspiration_after_first
    assert len(p1.hand) == hand_len_before


def test_no_attack_during_preparation_phase() -> None:
    engine = GameEngine.create_new(_cards(), "P1", "P2", "Animismo", "Animismo", seed=4)
    engine.start_turn()
    p1 = engine.state.players[0]
    saint_idx = _force_card_in_hand(engine, 0, "Guerriero")
    assert engine.play_card(0, saint_idx, "a1").ok
    out = engine.attack(0, 0, None)
    assert not out.ok


def test_equal_strength_and_faith_kills_defender_and_adds_sin() -> None:
    cards = [
        CardDefinition("Odino", "Santo", "8", 10, 8, "", "Mitologia Norrena"),
        CardDefinition("Sequoia", "Santo", "6", 8, 2, "", "Animismo"),
    ]
    engine = GameEngine.create_new(cards, "P1", "P2", "Mitologia Norrena", "Animismo", seed=11)
    _advance_to_active_phase(engine)
    while engine.state.active_player != 0:
        engine.end_turn()
        engine.start_turn()

    p1 = engine.state.players[0]
    p2 = engine.state.players[1]

    odino_idx = _force_card_in_hand(engine, 0, "Odino")
    assert engine.play_card(0, odino_idx, "a1").ok
    engine.end_turn()
    engine.start_turn()

    sequoia_idx = _force_card_in_hand(engine, 1, "Sequoia")
    assert engine.play_card(1, sequoia_idx, "a1").ok
    engine.end_turn()
    engine.start_turn()

    out = engine.attack(0, 0, 0)
    assert out.ok
    assert p2.attack[0] is None
    assert p2.sin >= 8


def test_invalid_attack_target_does_not_consume_attack() -> None:
    cards = [
        CardDefinition("Attaccante", "Santo", "3", 5, 5, "", "Animismo"),
        CardDefinition("Difensore", "Santo", "3", 5, 2, "", "Animismo"),
    ]
    engine = GameEngine.create_new(cards, "P1", "P2", "Animismo", "Animismo", seed=21)
    _advance_to_active_phase(engine)
    while engine.state.active_player != 0:
        engine.end_turn()
        engine.start_turn()

    p1 = engine.state.players[0]
    p2 = engine.state.players[1]
    a_idx = _force_card_in_hand(engine, 0, "Attaccante")
    assert engine.play_card(0, a_idx, "a1").ok
    engine.end_turn()
    engine.start_turn()
    d_idx = _force_card_in_hand(engine, 1, "Difensore")
    assert engine.play_card(1, d_idx, "a1").ok
    engine.end_turn()
    engine.start_turn()

    bad = engine.attack(0, 0, None)
    assert not bad.ok
    assert p1.attack[0] is not None
    assert not engine.state.instances[p1.attack[0]].exhausted

    good = engine.attack(0, 0, 0)
    assert good.ok


def test_pianta_carnivora_gets_bonus_with_insetto_della_palude() -> None:
    cards = [
        CardDefinition("Insetto della Palude", "Santo", "1", 2, 2, "", "ANI-1"),
        CardDefinition("Pianta Carnivora", "Santo", "3", 3, 3, "", "ANI-1"),
    ]
    engine = GameEngine.create_new(cards, "P1", "P2", "Animismo", "Animismo", seed=42)
    _advance_to_active_phase(engine)
    while engine.state.active_player != 0:
        engine.end_turn()
        engine.start_turn()
    p1 = engine.state.players[0]

    insetto_idx = _force_card_in_hand(engine, 0, "Insetto della Palude")
    assert engine.play_card(0, insetto_idx, "a1").ok
    pianta_idx = _force_card_in_hand(engine, 0, "Pianta Carnivora")
    assert engine.play_card(0, pianta_idx, "a2").ok

    pianta_uid = p1.attack[1]
    assert pianta_uid is not None
    pianta = engine.state.instances[pianta_uid]
    assert pianta.current_faith == 5
    assert engine.get_effective_strength(pianta_uid) == 5


def test_jordh_halves_incoming_damage_from_enemy_saints() -> None:
    cards = [
        CardDefinition("Attaccante", "Santo", "3", 10, 7, "", "NOR-1"),
        CardDefinition("Jordh", "Santo", "3", 8, 2, "", "NOR-1"),
        CardDefinition("Difensore", "Santo", "3", 10, 1, "", "NOR-1"),
    ]
    engine = GameEngine.create_new(cards, "P1", "P2", "NOR-1", "NOR-1", seed=77)
    _advance_to_active_phase(engine)
    while engine.state.active_player != 0:
        engine.end_turn()
        engine.start_turn()

    i_att = _force_card_in_hand(engine, 0, "Attaccante")
    assert engine.play_card(0, i_att, "a1").ok

    engine.end_turn()
    engine.start_turn()
    engine.state.players[1].inspiration = 20
    i_jordh = _force_card_in_hand(engine, 1, "Jordh")
    assert engine.play_card(1, i_jordh, "a1").ok
    i_def = _force_card_in_hand(engine, 1, "Difensore")
    assert engine.play_card(1, i_def, "a2").ok
    defender_uid = engine.state.players[1].attack[1]
    assert defender_uid is not None
    before = engine.state.instances[defender_uid].current_faith

    engine.end_turn()
    engine.start_turn()
    out = engine.attack(0, 0, 1)
    assert out.ok
    assert engine.state.instances[defender_uid].current_faith == max(0, (before or 0) - 3)


def test_loki_activate_sacrifices_without_sin_and_summons_from_hand() -> None:
    cards = [
        CardDefinition("Loki", "Santo", "5", 6, 2, "", "NOR-1"),
        CardDefinition("Jormungandr", "Santo", "10", 25, 6, "", "NOR-1"),
    ]
    engine = GameEngine.create_new(cards, "P1", "P2", "Mitologia Norrena", "Mitologia Norrena", seed=99)
    _advance_to_active_phase(engine)
    while engine.state.active_player != 0:
        engine.end_turn()
        engine.start_turn()
    p1 = engine.state.players[0]

    loki_idx = _force_card_in_hand(engine, 0, "Loki")
    assert engine.play_card(0, loki_idx, "a1").ok
    _force_card_in_hand(engine, 0, "Jormungandr")
    sin_before = p1.sin

    out = engine.activate_ability(0, "a1", "jormungandr")
    assert out.ok
    assert p1.sin == sin_before
    assert any(
        uid is not None and engine.state.instances[uid].definition.name == "Jormungandr"
        for uid in p1.attack + p1.defense
    )
    assert any(engine.state.instances[uid].definition.name == "Loki" for uid in p1.graveyard)


def test_direct_attack_not_allowed_if_defense_has_saints() -> None:
    cards = [
        CardDefinition("Attaccante", "Santo", "3", 5, 4, "", "Animismo"),
        CardDefinition("Difensore", "Santo", "3", 5, 2, "", "Animismo"),
    ]
    engine = GameEngine.create_new(cards, "P1", "P2", "Animismo", "Animismo", seed=55)
    _advance_to_active_phase(engine)
    while engine.state.active_player != 0:
        engine.end_turn()
        engine.start_turn()

    p1 = engine.state.players[0]
    a_idx = _force_card_in_hand(engine, 0, "Attaccante")
    assert engine.play_card(0, a_idx, "a1").ok
    engine.end_turn()
    engine.start_turn()
    d_idx = _force_card_in_hand(engine, 1, "Difensore")
    assert engine.play_card(1, d_idx, "d1").ok
    engine.end_turn()
    engine.start_turn()

    out = engine.attack(0, 0, None)
    assert not out.ok


def test_albero_fortunato_draws_two_on_death() -> None:
    cards = [
        CardDefinition("Killer", "Santo", "3", 5, 10, "", "Animismo"),
        CardDefinition("Albero Fortunato", "Santo", "2", 2, 1, "", "ANI-1"),
        CardDefinition("Riempitivo", "Santo", "2", 2, 1, "", "ANI-1"),
    ]
    engine = GameEngine.create_new(cards, "P1", "P2", "Animismo", "Animismo", seed=61)
    _advance_to_active_phase(engine)
    while engine.state.active_player != 0:
        engine.end_turn()
        engine.start_turn()
    p1 = engine.state.players[0]
    p2 = engine.state.players[1]
    killer_idx = _force_card_in_hand(engine, 0, "Killer")
    assert engine.play_card(0, killer_idx, "a1").ok
    engine.end_turn()
    engine.start_turn()
    target_idx = _force_card_in_hand(engine, 1, "Albero Fortunato")
    assert engine.play_card(1, target_idx, "a1").ok
    hand_before = len(p2.hand)
    engine.end_turn()
    engine.start_turn()
    assert engine.attack(0, 0, 0).ok
    assert len(p2.hand) >= hand_before + 1

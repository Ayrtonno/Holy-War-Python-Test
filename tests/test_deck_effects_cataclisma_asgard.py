from __future__ import annotations

from holywar.core.engine import GameEngine
from holywar.data.models import CardDefinition


def _advance_to_active(engine: GameEngine) -> None:
    engine.start_turn()
    engine.end_turn()
    engine.start_turn()
    engine.end_turn()
    if engine.state.phase == 'active':
        engine.start_turn()


def _force_card_in_hand(engine: GameEngine, player_idx: int, name: str) -> int:
    player = engine.state.players[player_idx]
    for i, uid in enumerate(player.hand):
        if engine.state.instances[uid].definition.name == name:
            return i
    for i, uid in enumerate(player.deck):
        if engine.state.instances[uid].definition.name == name:
            moved = player.deck.pop(i)
            player.hand.append(moved)
            return len(player.hand) - 1
    raise AssertionError(name)


def test_concentrazione_draws_two_cards() -> None:
    cards = [
        CardDefinition('Concentrazione', 'Benedizione', '3', None, None, '', 'NEU-1'),
        CardDefinition('Seguace', 'Santo', '2', 5, 2, '', 'NEU-1'),
    ]
    engine = GameEngine.create_new(cards, 'P1', 'P2', 'Cristianesimo', 'Cristianesimo', seed=1)
    _advance_to_active(engine)
    if engine.state.active_player != 0:
        engine.end_turn(); engine.start_turn()
    p1 = engine.state.players[0]
    while len(p1.hand) > 6:
        p1.deck.insert(0, p1.hand.pop())
    hand_before = len(p1.hand)
    idx = _force_card_in_hand(engine, 0, 'Concentrazione')
    assert engine.play_card(0, idx, None).ok
    assert len(p1.hand) >= hand_before + 1


def test_mjolnir_requires_jarngreipr() -> None:
    cards = [
        CardDefinition('Mjolnir', 'Artefatto', '8', 8, None, '', 'NOR-1'),
        CardDefinition('Járngreipr', 'Artefatto', '4', 4, None, '', 'NOR-1'),
    ]
    engine = GameEngine.create_new(cards, 'P1', 'P2', 'Mitologia Norrena', 'Mitologia Norrena', seed=2)
    _advance_to_active(engine)
    if engine.state.active_player != 0:
        engine.end_turn(); engine.start_turn()
    engine.state.players[0].inspiration = 30
    idx = _force_card_in_hand(engine, 0, 'Mjolnir')
    bad = engine.play_card(0, idx, None)
    assert not bad.ok
    jidx = _force_card_in_hand(engine, 0, 'Járngreipr')
    assert engine.play_card(0, jidx, None).ok
    midx = _force_card_in_hand(engine, 0, 'Mjolnir')
    assert engine.play_card(0, midx, None).ok


def test_tanngnjostr_activate_buffs_thor_without_sin() -> None:
    cards = [
        CardDefinition('Thor', 'Santo', '9', 10, 8, '', 'NOR-1'),
        CardDefinition('Tanngnjostr', 'Santo', '2', 2, 3, '', 'NOR-1'),
    ]
    engine = GameEngine.create_new(cards, 'P1', 'P2', 'Mitologia Norrena', 'Mitologia Norrena', seed=3)
    _advance_to_active(engine)
    if engine.state.active_player != 0:
        engine.end_turn(); engine.start_turn()
    p1 = engine.state.players[0]
    p1.inspiration = 30
    thor_idx = _force_card_in_hand(engine, 0, 'Thor')
    assert engine.play_card(0, thor_idx, 'a1').ok
    tan_idx = _force_card_in_hand(engine, 0, 'Tanngnjostr')
    assert engine.play_card(0, tan_idx, 'a2').ok
    sin_before = p1.sin
    out = engine.activate_ability(0, 'a2', None)
    assert out.ok
    assert p1.sin == sin_before
    thor_uid = p1.attack[0]
    assert thor_uid is not None
    assert (engine.state.instances[thor_uid].current_faith or 0) >= 14


def test_thor_survives_battle_with_tanng_in_grave() -> None:
    cards = [
        CardDefinition('Thor', 'Santo', '9', 10, 8, '', 'NOR-1'),
        CardDefinition('Tanngrisnir', 'Santo', '2', 2, 3, '', 'NOR-1'),
        CardDefinition('Nemico', 'Santo', '3', 5, 20, '', 'Animismo'),
    ]
    engine = GameEngine.create_new(cards, 'P1', 'P2', 'Mitologia Norrena', 'Animismo', seed=4)
    _advance_to_active(engine)
    while engine.state.active_player != 0:
        engine.end_turn(); engine.start_turn()
    p1 = engine.state.players[0]
    p2 = engine.state.players[1]
    p1.inspiration = 30
    t_idx = _force_card_in_hand(engine, 0, 'Thor')
    assert engine.play_card(0, t_idx, 'a1').ok
    g_idx = _force_card_in_hand(engine, 0, 'Tanngrisnir')
    assert engine.play_card(0, g_idx, 'd1').ok
    # put tanngrisnir in grave (effect-like)
    t_uid = p1.defense[0]
    assert t_uid is not None
    engine.remove_from_board_no_sin(0, t_uid)
    engine.end_turn(); engine.start_turn()
    n_idx = _force_card_in_hand(engine, 1, 'Nemico')
    assert engine.play_card(1, n_idx, 'a1').ok
    engine.end_turn(); engine.start_turn()
    while engine.state.active_player != 1:
        engine.end_turn()
        engine.start_turn()
    assert engine.attack(1, 0, 0).ok
    assert p1.attack[0] is not None
    assert engine.state.instances[p1.attack[0]].definition.name == 'Thor'
    assert (engine.state.instances[p1.attack[0]].current_faith or 0) == 4


def test_cataclisma_ciclico_triggers_at_turn_start() -> None:
    cards = [
        CardDefinition('Cataclisma Ciclico', 'Artefatto', '9', 6, None, '', 'ANI-1'),
        CardDefinition('Seguace', 'Santo', '2', 5, 2, '', 'NEU-1'),
    ]
    engine = GameEngine.create_new(cards, 'P1', 'P2', 'Animismo', 'Cristianesimo', seed=5)
    _advance_to_active(engine)
    if engine.state.active_player != 0:
        engine.end_turn(); engine.start_turn()
    p1 = engine.state.players[0]
    p2 = engine.state.players[1]
    c_idx = _force_card_in_hand(engine, 0, 'Cataclisma Ciclico')
    assert engine.play_card(0, c_idx, None).ok
    s_idx = _force_card_in_hand(engine, 1, 'Seguace')
    engine.end_turn(); engine.start_turn()
    assert engine.play_card(1, s_idx, 'a1').ok
    engine.end_turn()
    # start turn P1 => cataclisma should trigger and kill opponent saint, reducing P1 sin by 1 (floor 0)
    engine.start_turn()
    assert p2.attack[0] is None


def test_vulcano_activate_once_per_turn() -> None:
    cards = [
        CardDefinition('Vulcano', 'Santo', '10', 25, 15, '', 'ANI-1'),
        CardDefinition('Dummy', 'Santo', '2', 3, 1, '', 'NEU-1'),
    ]
    engine = GameEngine.create_new(cards, 'P1', 'P2', 'Animismo', 'Cristianesimo', seed=6)
    _advance_to_active(engine)
    if engine.state.active_player != 0:
        engine.end_turn(); engine.start_turn()
    p1 = engine.state.players[0]
    p2 = engine.state.players[1]
    # bypass normal summon rule for controlled test
    v_uid = next(uid for uid in p1.deck if engine.state.instances[uid].definition.name == 'Vulcano')
    p1.deck.remove(v_uid)
    p1.attack[0] = v_uid
    d_uid = next(uid for uid in p2.deck if engine.state.instances[uid].definition.name == 'Dummy')
    p2.deck.remove(d_uid)
    p2.attack[0] = d_uid
    out1 = engine.activate_ability(0, 'a1', 'o:a1')
    out2 = engine.activate_ability(0, 'a1', 'o:a1')
    assert out1.ok
    assert out2.ok
    assert 'gia usata' in out2.message.lower()

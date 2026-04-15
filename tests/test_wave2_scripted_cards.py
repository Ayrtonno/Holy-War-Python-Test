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


def test_kah_ok_tick_is_scripted_and_self_destroys_at_10() -> None:
    cards = [
        CardDefinition("Kah-ok", "Santo", "1", 8, 1, "", "PHD-1"),
        CardDefinition("Fill", "Santo", "1", 1, 1, "", "PHD-1"),
    ]
    engine = GameEngine.create_new(cards, "P1", "P2", "PHD-1", "PHD-1", seed=601)
    _advance_to_active_phase(engine)
    while engine.state.active_player != 0:
        engine.end_turn()
        engine.start_turn()
    i = _force_card_in_hand(engine, 0, "Kah-ok")
    assert engine.play_card(0, i, "a1").ok
    uid = engine.state.players[0].attack[0]
    assert uid is not None
    engine.state.instances[uid].current_faith = 8
    sin_before = engine.state.players[0].sin
    engine.end_turn()
    engine.start_turn()
    engine.end_turn()
    engine.start_turn()
    assert engine.state.players[0].attack[0] is None
    assert engine.state.players[0].sin >= sin_before + 10


def test_trombe_del_giudizio_inflicts_sin_based_on_altar_seals() -> None:
    cards = [
        CardDefinition("Altare dei Sette Sigilli", "Edificio", "1", 1, None, "", "CRI-1"),
        CardDefinition("Trombe del Giudizio", "Artefatto", "1", 1, None, "", "CRI-1"),
        CardDefinition("Fill", "Santo", "1", 1, 1, "", "CRI-1"),
    ]
    engine = GameEngine.create_new(cards, "P1", "P2", "CRI-1", "CRI-1", seed=602)
    _advance_to_active_phase(engine)
    while engine.state.active_player != 0:
        engine.end_turn()
        engine.start_turn()
    b = _force_card_in_hand(engine, 0, "Altare dei Sette Sigilli")
    assert engine.play_card(0, b, None).ok
    t = _force_card_in_hand(engine, 0, "Trombe del Giudizio")
    assert engine.play_card(0, t, None).ok
    engine._set_altare_sigilli(0, 5)
    sin_before = engine.state.players[1].sin
    engine.end_turn()
    engine.start_turn()
    engine.end_turn()
    engine.start_turn()
    assert engine.state.players[1].sin >= sin_before + 6


def test_radici_gives_plus_two_faith_to_tree_cards_each_own_turn() -> None:
    cards = [
        CardDefinition("Radici", "Artefatto", "1", 1, None, "", "ANI-1"),
        CardDefinition("Albero Sacro", "Santo", "1", 3, 1, "", "ANI-1"),
        CardDefinition("Fill", "Santo", "1", 1, 1, "", "ANI-1"),
    ]
    engine = GameEngine.create_new(cards, "P1", "P2", "ANI-1", "ANI-1", seed=603)
    _advance_to_active_phase(engine)
    while engine.state.active_player != 0:
        engine.end_turn()
        engine.start_turn()
    r = _force_card_in_hand(engine, 0, "Radici")
    assert engine.play_card(0, r, None).ok
    a = _force_card_in_hand(engine, 0, "Albero Sacro")
    assert engine.play_card(0, a, "a1").ok
    uid = engine.state.players[0].attack[0]
    assert uid is not None
    before = engine.state.instances[uid].current_faith or 0
    engine.end_turn()
    engine.start_turn()
    engine.end_turn()
    engine.start_turn()
    after = engine.state.instances[uid].current_faith or 0
    assert after >= before + 2


def test_av_drna_ticks_on_opponent_draw_and_self_destroys_at_zero_faith() -> None:
    cards = [
        CardDefinition("Av'drna", "Edificio", "1", 2, None, "", "PHD-1"),
        CardDefinition("Fill", "Santo", "1", 1, 1, "", "PHD-1"),
    ]
    engine = GameEngine.create_new(cards, "P1", "P2", "PHD-1", "PHD-1", seed=604)
    _advance_to_active_phase(engine)
    while engine.state.active_player != 0:
        engine.end_turn()
        engine.start_turn()
    b = _force_card_in_hand(engine, 0, "Av'drna")
    assert engine.play_card(0, b, None).ok
    bid = engine.state.players[0].building
    assert bid is not None
    engine.state.players[0].sin = 10
    faith_before = engine.state.instances[bid].current_faith or 0
    engine.draw_cards(1, 1)
    faith_after = engine.state.instances[bid].current_faith or 0
    assert faith_after == max(0, faith_before - 1)
    assert engine.state.players[0].sin <= 8
    # second opponent draw should destroy Av'drna (faith reaches 0)
    engine.draw_cards(1, 1)
    assert engine.state.players[0].building is None


def test_deriu_hebet_draws_top_if_blessing_or_curse() -> None:
    cards = [
        CardDefinition("Deriu-hebet", "Santo", "1", 3, 1, "", "EGI-1"),
        CardDefinition("BlessX", "Benedizione", "1", None, None, "", "EGI-1"),
        CardDefinition("Fill", "Santo", "1", 1, 1, "", "EGI-1"),
    ]
    engine = GameEngine.create_new(cards, "P1", "P2", "EGI-1", "EGI-1", seed=605)
    _advance_to_active_phase(engine)
    while engine.state.active_player != 0:
        engine.end_turn()
        engine.start_turn()
    d = _force_card_in_hand(engine, 0, "Deriu-hebet")
    assert engine.play_card(0, d, "a1").ok
    # Ensure top deck is blessing for deterministic trigger outcome.
    p0 = engine.state.players[0]
    bless_uid = next(uid for uid in p0.deck if engine.state.instances[uid].definition.name == "BlessX")
    p0.deck.remove(bless_uid)
    p0.deck.append(bless_uid)
    hand_before = len(p0.hand)
    engine.end_turn()
    engine.start_turn()
    engine.end_turn()
    engine.start_turn()
    hand_after = len(p0.hand)
    assert hand_after >= hand_before + 1


def test_spirito_dell_esercito_dorato_requires_five_sin_upkeep() -> None:
    cards = [
        CardDefinition("Spirito dell'Esercito Dorato", "Artefatto", "1", 1, None, "", "MAY-1"),
        CardDefinition("Fill", "Santo", "1", 1, 1, "", "MAY-1"),
    ]
    engine = GameEngine.create_new(cards, "P1", "P2", "MAY-1", "MAY-1", seed=606)
    _advance_to_active_phase(engine)
    while engine.state.active_player != 0:
        engine.end_turn()
        engine.start_turn()
    s = _force_card_in_hand(engine, 0, "Spirito dell'Esercito Dorato")
    assert engine.play_card(0, s, None).ok
    uid = next(uid for uid in engine.state.players[0].artifacts if uid is not None)
    assert uid is not None
    engine.state.players[0].sin = 4
    engine.end_turn()
    engine.start_turn()
    engine.end_turn()
    engine.start_turn()
    assert uid not in engine.state.players[0].artifacts


def test_tikal_adds_top_saint_to_hand_or_moves_top_card_to_bottom() -> None:
    cards = [
        CardDefinition("Tikal", "Edificio", "1", 1, None, "", "MAY-1"),
        CardDefinition("TopSaint", "Santo", "1", 1, 1, "", "MAY-1"),
        CardDefinition("TopSpell", "Benedizione", "1", None, None, "", "MAY-1"),
        CardDefinition("Fill", "Santo", "1", 1, 1, "", "MAY-1"),
    ]
    engine = GameEngine.create_new(cards, "P1", "P2", "MAY-1", "MAY-1", seed=607)
    _advance_to_active_phase(engine)
    while engine.state.active_player != 0:
        engine.end_turn()
        engine.start_turn()
    t = _force_card_in_hand(engine, 0, "Tikal")
    assert engine.play_card(0, t, None).ok
    p0 = engine.state.players[0]

    saint_uid = next(uid for uid in p0.deck if engine.state.instances[uid].definition.name == "TopSaint")
    p0.deck.remove(saint_uid)
    p0.deck.append(saint_uid)
    hand_before = len(p0.hand)
    engine.end_turn()
    engine.start_turn()
    engine.end_turn()
    engine.start_turn()
    assert len(p0.hand) >= hand_before + 1

    spell_uid = next(uid for uid in p0.deck if engine.state.instances[uid].definition.name == "TopSpell")
    p0.deck.remove(spell_uid)
    p0.deck.append(spell_uid)
    engine.end_turn()
    engine.start_turn()
    engine.end_turn()
    engine.start_turn()
    assert p0.deck[0] == spell_uid

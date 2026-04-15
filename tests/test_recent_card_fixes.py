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


def test_cura_rapida_requires_two_targets_and_heals_plus_three_each() -> None:
    cards = [
        CardDefinition("S1", "Santo", "2", 5, 1, "", "NEU-1"),
        CardDefinition("S2", "Santo", "2", 5, 1, "", "NEU-1"),
        CardDefinition("Cura Rapida", "Benedizione", "1", None, None, "Due tuoi Santi bersaglio ricevono +3 Fede ciascuno.", "NEU-1"),
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
    out = engine.play_card(0, q, "a1,a2")
    assert out.ok
    assert engine.state.instances[uid1].current_faith == 5
    assert engine.state.instances[uid2].current_faith == 4


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


def test_ricerca_archeologica_accepts_deck_prefixed_target() -> None:
    cards = [
        CardDefinition("A1", "Artefatto", "1", 1, None, "", "NEU-1"),
        CardDefinition("A2", "Artefatto", "1", 1, None, "", "NEU-1"),
        CardDefinition("Ricerca Archeologica", "Benedizione", "1", None, None, "Cerca un artefatto nel reliquiario.", "NEU-1"),
    ]
    engine = GameEngine.create_new(cards, "P1", "P2", "NEU-1", "NEU-1", seed=7)
    _advance_to_active_phase(engine)
    while engine.state.active_player != 0:
        engine.end_turn()
        engine.start_turn()
    q = _force_card_in_hand(engine, 0, "Ricerca Archeologica")
    out = engine.play_card(0, q, "deck:A2")
    assert out.ok
    hand_names = [engine.state.instances[uid].definition.name for uid in engine.state.players[0].hand]
    assert "A2" in hand_names


def test_ricerca_archeologica_without_target_requires_choice_if_multiple_artifacts() -> None:
    cards = [
        CardDefinition("A1", "Artefatto", "1", 1, None, "", "NEU-1"),
        CardDefinition("A2", "Artefatto", "1", 1, None, "", "NEU-1"),
        CardDefinition("Ricerca Archeologica", "Benedizione", "1", None, None, "Cerca un artefatto nel reliquiario.", "NEU-1"),
    ]
    engine = GameEngine.create_new(cards, "P1", "P2", "NEU-1", "NEU-1", seed=8)
    _advance_to_active_phase(engine)
    while engine.state.active_player != 0:
        engine.end_turn()
        engine.start_turn()
    q = _force_card_in_hand(engine, 0, "Ricerca Archeologica")
    out = engine.play_card(0, q, None)
    assert out.ok
    assert "scegli un artefatto" in out.message.lower()


def test_ricerca_archeologica_autopicks_if_only_one_artifact() -> None:
    cards = [
        CardDefinition("A1", "Artefatto", "1", 1, None, "", "NEU-1"),
        CardDefinition("S1", "Santo", "2", 5, 1, "", "NEU-1"),
        CardDefinition("Ricerca Archeologica", "Benedizione", "1", None, None, "Cerca un artefatto nel reliquiario.", "NEU-1"),
    ]
    engine = GameEngine.create_new(cards, "P1", "P2", "NEU-1", "NEU-1", seed=9)
    _advance_to_active_phase(engine)
    while engine.state.active_player != 0:
        engine.end_turn()
        engine.start_turn()
    p1 = engine.state.players[0]
    first_artifact_uid = next(
        uid for uid in p1.deck if engine.state.instances[uid].definition.card_type.lower() == "artefatto"
    )
    p1.deck = [
        uid
        for uid in p1.deck
        if engine.state.instances[uid].definition.card_type.lower() != "artefatto" or uid == first_artifact_uid
    ]
    q = _force_card_in_hand(engine, 0, "Ricerca Archeologica")
    out = engine.play_card(0, q, None)
    assert out.ok
    hand_names = [engine.state.instances[uid].definition.name for uid in engine.state.players[0].hand]
    assert "A1" in hand_names


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


def test_zero_faith_saint_is_not_kept_on_field_after_action() -> None:
    cards = [
        CardDefinition("S1", "Santo", "2", 5, 1, "", "NEU-1"),
    ]
    engine = GameEngine.create_new(cards, "P1", "P2", "NEU-1", "NEU-1", seed=11)
    _advance_to_active_phase(engine)
    while engine.state.active_player != 0:
        engine.end_turn()
        engine.start_turn()
    idx = _force_card_in_hand(engine, 0, "S1")
    assert engine.play_card(0, idx, "a1").ok
    uid = engine.state.players[0].attack[0]
    assert uid is not None
    engine.state.instances[uid].current_faith = 0
    engine.end_turn()
    assert engine.state.players[0].attack[0] is None


def test_figli_di_odino_buffs_targeted_own_saint() -> None:
    cards = [
        CardDefinition("Odino", "Santo", "3", 1, 2, "", "NOR-1"),
        CardDefinition("Thor", "Santo", "3", 1, 2, "", "NOR-1"),
        CardDefinition("Target", "Santo", "2", 1, 1, "", "NOR-1"),
        CardDefinition(
            "Figli di Odino",
            "Benedizione",
            "1",
            None,
            None,
            "Un Santo bersaglio riceve +3 Forza. Se controlli Odino, quel Santo riceve +6 Forza invece.",
            "NOR-1",
        ),
    ]
    engine = GameEngine.create_new(cards, "P1", "P2", "NOR-1", "NOR-1", seed=12)
    _advance_to_active_phase(engine)
    while engine.state.active_player != 0:
        engine.end_turn()
        engine.start_turn()
    i_odino = _force_card_in_hand(engine, 0, "Odino")
    assert engine.play_card(0, i_odino, "a1").ok
    i_thor = _force_card_in_hand(engine, 0, "Thor")
    assert engine.play_card(0, i_thor, "a2").ok
    i_tgt = _force_card_in_hand(engine, 0, "Target")
    assert engine.play_card(0, i_tgt, "a3").ok
    uid_tgt = engine.state.players[0].attack[2]
    assert uid_tgt is not None
    before = engine.get_effective_strength(uid_tgt)
    i_spell = _force_card_in_hand(engine, 0, "Figli di Odino")
    out = engine.play_card(0, i_spell, "a3")
    assert out.ok
    after = engine.get_effective_strength(uid_tgt)
    assert after >= before + 6


def test_saga_degli_eroi_caduti_buffs_only_own_saints_on_field() -> None:
    cards = [
        CardDefinition("Saga degli Eroi Caduti", "Artefatto", "4", 0, None, "", "NOR-1"),
        CardDefinition("S1", "Santo", "2", 5, 1, "", "NOR-1"),
        CardDefinition("S2", "Santo", "2", 5, 1, "", "NOR-1"),
        CardDefinition("S3", "Santo", "2", 5, 1, "", "NOR-1"),
        CardDefinition("Enemy", "Santo", "2", 5, 1, "", "ANI-1"),
    ]
    engine = GameEngine.create_new(cards, "P1", "P2", "NOR-1", "ANI-1", seed=13)
    _advance_to_active_phase(engine)
    while engine.state.active_player != 0:
        engine.end_turn()
        engine.start_turn()
    i_saga = _force_card_in_hand(engine, 0, "Saga degli Eroi Caduti")
    assert engine.play_card(0, i_saga, None).ok
    i1 = _force_card_in_hand(engine, 0, "S1")
    assert engine.play_card(0, i1, "a1").ok
    i2 = _force_card_in_hand(engine, 0, "S2")
    assert engine.play_card(0, i2, "a2").ok
    uid1 = engine.state.players[0].attack[0]
    uid2 = engine.state.players[0].attack[1]
    assert uid1 and uid2
    i_enemy = _force_card_in_hand(engine, 1, "Enemy")
    engine.end_turn()
    assert engine.play_card(1, i_enemy, "a1").ok
    enemy_uid = engine.state.players[1].attack[0]
    assert enemy_uid is not None
    engine.end_turn()
    # Force destruction of S1; cleanup at end_turn triggers Saga.
    engine.state.instances[uid1].current_faith = 0
    engine.end_turn()
    assert engine.state.players[0].attack[0] is None
    assert engine.get_effective_strength(uid2) >= 2
    # Future saint should not inherit previous saga buffs.
    while engine.state.active_player != 0:
        engine.end_turn()
    engine.start_turn()
    i3 = _force_card_in_hand(engine, 0, "S3")
    assert engine.play_card(0, i3, "a1").ok
    uid3 = engine.state.players[0].attack[0]
    assert uid3 is not None
    assert engine.get_effective_strength(uid3) == 1
    # Opponent saint should not get buff from our saga.
    assert engine.get_effective_strength(enemy_uid) == 1


def test_monsone_discards_hand_then_deck_and_returns_selected_cards_to_owner_decks() -> None:
    cards = [
        CardDefinition("Monsone", "Maledizione", "2", None, None, "", "ANI-1"),
        CardDefinition("H1", "Santo", "2", 1, 1, "", "ANI-1"),
        CardDefinition("H2", "Santo", "2", 1, 1, "", "ANI-1"),
        CardDefinition("D1", "Santo", "2", 1, 1, "", "ANI-1"),
        CardDefinition("OwnBoard", "Santo", "2", 1, 1, "", "ANI-1"),
        CardDefinition("OppBoard", "Santo", "2", 1, 1, "", "ANI-1"),
    ]
    engine = GameEngine.create_new(cards, "P1", "P2", "ANI-1", "ANI-1", seed=21)
    _advance_to_active_phase(engine)
    while engine.state.active_player != 0:
        engine.end_turn()
        engine.start_turn()

    p0 = engine.state.players[0]
    p1 = engine.state.players[1]

    i_own = _force_card_in_hand(engine, 0, "OwnBoard")
    assert engine.play_card(0, i_own, "a1").ok
    own_uid = p0.attack[0]
    assert own_uid is not None

    engine.end_turn()
    engine.start_turn()
    i_opp = _force_card_in_hand(engine, 1, "OppBoard")
    assert engine.play_card(1, i_opp, "a1").ok
    opp_uid = p1.attack[0]
    assert opp_uid is not None
    engine.end_turn()
    engine.start_turn()

    i_h1 = _force_card_in_hand(engine, 0, "H1")
    h1_uid = p0.hand[i_h1]
    i_h2 = _force_card_in_hand(engine, 0, "H2")
    h2_uid = p0.hand[i_h2]
    _force_card_in_hand(engine, 0, "D1")
    top_before = p0.deck[-1]
    i_monsone = _force_card_in_hand(engine, 0, "Monsone")
    target = f"monsone:discard={h1_uid},{h2_uid};return={own_uid},{opp_uid}"
    out = engine.play_card(0, i_monsone, target)
    assert out.ok

    assert h1_uid in p0.graveyard
    assert h2_uid in p0.graveyard
    assert top_before in p0.graveyard
    assert own_uid in p0.deck
    assert opp_uid in p1.deck
    assert own_uid not in (p0.attack + p0.defense + p0.artifacts)
    assert opp_uid not in (p1.attack + p1.defense + p1.artifacts)

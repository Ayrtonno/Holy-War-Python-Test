from __future__ import annotations

from holywar.core.engine import GameEngine
from holywar.effects.runtime import CardFilterSpec, TargetSpec, runtime_cards
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


def test_ricerca_archeologica_without_target_fails_even_if_artifacts_exist() -> None:
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
    assert not out.ok
    assert "selezionare almeno un bersaglio valido" in out.message.lower()


def test_ricerca_archeologica_requires_explicit_target_even_if_only_one_artifact() -> None:
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
    assert not out.ok
    assert "selezionare almeno un bersaglio valido" in out.message.lower()


def test_risveglio_di_ph_dak_gaph_cannot_be_played_without_excommunicated_targets() -> None:
    cards = [
        CardDefinition("Risveglio di Ph-Dak'Gaph", "Benedizione", "1", None, None, "", "PHD-1"),
        CardDefinition("Fill", "Santo", "1", 1, 1, "", "PHD-1"),
    ]
    engine = GameEngine.create_new(cards, "P1", "P2", "PHD-1", "PHD-1", seed=122)
    _advance_to_active_phase(engine)
    while engine.state.active_player != 0:
        engine.end_turn()
        engine.start_turn()
    idx = _force_card_in_hand(engine, 0, "Risveglio di Ph-Dak'Gaph")
    out = engine.play_card(0, idx, None)
    assert not out.ok
    assert "nessun bersaglio valido disponibile" in out.message.lower()


def test_ricerca_archeologica_is_scripted_with_shuffle() -> None:
    script = runtime_cards.get_script("Ricerca Archeologica")
    assert script is not None
    first_target = script.on_play_actions[0].target
    assert first_target.type == "selected_target"
    assert first_target.zone == "relicario"
    assert first_target.owner == "me"
    assert first_target.card_filter.card_type_in == ["artefatto"]
    assert first_target.min_targets == 1
    assert first_target.max_targets == 1
    assert [a.effect.action for a in script.on_play_actions] == [
        "move_to_hand",
        "shuffle_deck",
    ]

    cards = [
        CardDefinition("A1", "Artefatto", "1", 1, None, "", "NEU-1"),
        CardDefinition("A2", "Artefatto", "1", 1, None, "", "NEU-1"),
        CardDefinition("Ricerca Archeologica", "Benedizione", "1", None, None, "Cerca un artefatto nel reliquiario.", "NEU-1"),
    ]
    engine = GameEngine.create_new(cards, "P1", "P2", "NEU-1", "NEU-1", seed=10)
    _advance_to_active_phase(engine)
    while engine.state.active_player != 0:
        engine.end_turn()
        engine.start_turn()
    q = _force_card_in_hand(engine, 0, "Ricerca Archeologica")
    out = engine.play_card(0, q, "deck:A2")
    assert out.ok
    hand_names = [engine.state.instances[uid].definition.name for uid in engine.state.players[0].hand]
    assert "A2" in hand_names


def test_risveglio_di_ph_dak_gaph_recovers_up_to_five_and_excommunicates_itself() -> None:
    script = runtime_cards.get_script("Risveglio di Ph-Dak'Gaph")
    assert script is not None
    assert [a.effect.action for a in script.on_play_actions] == [
        "move_to_hand",
        "remove_sin",
        "move_source_to_zone",
    ]

    cards = [
        CardDefinition("Risveglio di Ph-Dak'Gaph", "Benedizione", "1", None, None, "", "PHD-1"),
        CardDefinition("Ex1", "Benedizione", "1", None, None, "", "PHD-1"),
        CardDefinition("Ex2", "Maledizione", "1", None, None, "", "PHD-1"),
        CardDefinition("Ex3", "Artefatto", "1", 1, None, "", "PHD-1"),
        CardDefinition("Ex4", "Santo", "1", 1, 1, "", "PHD-1"),
        CardDefinition("Ex5", "Benedizione", "1", None, None, "", "PHD-1"),
        CardDefinition("Ex6", "Maledizione", "1", None, None, "", "PHD-1"),
    ]
    engine = GameEngine.create_new(cards, "P1", "P2", "PHD-1", "PHD-1", seed=121)
    _advance_to_active_phase(engine)
    while engine.state.active_player != 0:
        engine.end_turn()
        engine.start_turn()

    p0 = engine.state.players[0]
    ris_idx = _force_card_in_hand(engine, 0, "Risveglio di Ph-Dak'Gaph")
    ris_uid = p0.hand[ris_idx]
    for uid in list(p0.hand):
        if uid == ris_uid:
            continue
        p0.hand.remove(uid)
        p0.deck.append(uid)
    ris_idx = p0.hand.index(ris_uid)

    ex_names = {"Ex1", "Ex2", "Ex3", "Ex4", "Ex5", "Ex6"}
    ex_uids: list[str] = []
    for uid in list(p0.deck):
        if engine.state.instances[uid].definition.name in ex_names:
            p0.deck.remove(uid)
            p0.excommunicated.append(uid)
            ex_uids.append(uid)
        if len(ex_uids) == 6:
            break
    assert len(ex_uids) == 6

    chosen = ex_uids[:5]
    keep = ex_uids[5]
    p0.sin = 20

    out = engine.play_card(0, ris_idx, ",".join(chosen))
    assert out.ok

    for uid in chosen:
        assert uid in p0.hand
        assert uid not in p0.excommunicated
    assert keep in p0.excommunicated
    assert p0.sin == 10
    assert ris_uid in p0.excommunicated
    assert ris_uid not in p0.graveyard


def test_rito_della_ri_manifestazione_is_scripted_and_moves_excommunicated_to_relicario() -> None:
    script = runtime_cards.get_script("Rito della Ri-Manifestazione")
    assert script is not None
    assert [a.effect.action for a in script.on_play_actions] == [
        "move_to_relicario",
        "shuffle_deck",
        "draw_cards",
    ]
    tgt = script.on_play_actions[0].target
    assert tgt.type == "selected_targets"
    assert tgt.zone == "excommunicated"
    assert tgt.owner == "me"
    assert tgt.min_targets == 1
    assert tgt.max_targets == 3

    cards = [
        CardDefinition("Rito della Ri-Manifestazione", "Benedizione", "1", None, None, "", "PHD-1"),
        CardDefinition("Ex1", "Santo", "1", 1, 1, "", "PHD-1"),
        CardDefinition("Ex2", "Artefatto", "1", 1, None, "", "PHD-1"),
        CardDefinition("Ex3", "Benedizione", "1", None, None, "", "PHD-1"),
        CardDefinition("Ex4", "Maledizione", "1", None, None, "", "PHD-1"),
        CardDefinition("Fill", "Santo", "1", 1, 1, "", "PHD-1"),
    ]
    engine = GameEngine.create_new(cards, "P1", "P2", "PHD-1", "PHD-1", seed=123)
    _advance_to_active_phase(engine)
    while engine.state.active_player != 0:
        engine.end_turn()
        engine.start_turn()

    p0 = engine.state.players[0]
    idx = _force_card_in_hand(engine, 0, "Rito della Ri-Manifestazione")
    rito_uid = p0.hand[idx]
    for uid in list(p0.hand):
        if uid == rito_uid:
            continue
        p0.hand.remove(uid)
        p0.deck.append(uid)
    idx = p0.hand.index(rito_uid)

    ex_names = {"Ex1", "Ex2", "Ex3", "Ex4"}
    ex_uids: list[str] = []
    for uid in list(p0.deck):
        if engine.state.instances[uid].definition.name in ex_names:
            p0.deck.remove(uid)
            p0.excommunicated.append(uid)
            ex_uids.append(uid)
    assert len(ex_uids) >= 4

    chosen = ex_uids[:3]
    before_hand = len(p0.hand)
    out = engine.play_card(0, idx, ",".join(chosen))
    assert out.ok
    # No Av'drna/Ph'drna controlled: no extra draw.
    assert len(p0.hand) == before_hand - 1

    for uid in chosen:
        assert uid not in p0.excommunicated
        assert uid in p0.deck
    assert ex_uids[3] in p0.excommunicated


def test_rito_della_ri_manifestazione_draws_if_controller_has_avdrna_or_phdrna() -> None:
    cards = [
        CardDefinition("Rito della Ri-Manifestazione", "Benedizione", "1", None, None, "", "PHD-1"),
        CardDefinition("Av'drna", "Edificio", "1", 2, None, "", "PHD-1"),
        CardDefinition("Ex1", "Santo", "1", 1, 1, "", "PHD-1"),
        CardDefinition("Fill", "Santo", "1", 1, 1, "", "PHD-1"),
    ]
    engine = GameEngine.create_new(cards, "P1", "P2", "PHD-1", "PHD-1", seed=124)
    _advance_to_active_phase(engine)
    while engine.state.active_player != 0:
        engine.end_turn()
        engine.start_turn()

    p0 = engine.state.players[0]
    av_idx = _force_card_in_hand(engine, 0, "Av'drna")
    assert engine.play_card(0, av_idx, None).ok

    rito_idx = _force_card_in_hand(engine, 0, "Rito della Ri-Manifestazione")
    rito_uid = p0.hand[rito_idx]
    for uid in list(p0.hand):
        if uid == rito_uid:
            continue
        p0.hand.remove(uid)
        p0.deck.append(uid)
    rito_idx = p0.hand.index(rito_uid)

    ex_uid = next(uid for uid in p0.deck if engine.state.instances[uid].definition.name == "Ex1")
    p0.deck.remove(ex_uid)
    p0.excommunicated.append(ex_uid)

    before_hand = len(p0.hand)
    out = engine.play_card(0, rito_idx, ex_uid)
    assert out.ok
    # Controlled Av'drna: card draw compensates the spent quick card.
    assert len(p0.hand) == before_hand
    assert ex_uid not in p0.excommunicated
    assert ex_uid in p0.deck or ex_uid in p0.hand


def test_rito_funebre_is_scripted_and_can_target_saint_in_any_graveyard() -> None:
    script = runtime_cards.get_script("Rito Funebre")
    assert script is not None
    assert [a.effect.action for a in script.on_play_actions] == [
        "move_to_relicario",
        "shuffle_target_owner_decks",
    ]
    tgt = script.on_play_actions[0].target
    assert tgt.type == "selected_target"
    assert tgt.zone == "graveyard"
    assert tgt.owner == "any"
    assert tgt.card_filter.card_type_in == ["santo"]
    assert tgt.min_targets == 1
    assert tgt.max_targets == 1

    cards = [
        CardDefinition("Rito Funebre", "Benedizione", "1", None, None, "", "ANI-1"),
        CardDefinition("DeadSaint", "Santo", "2", 2, 1, "", "ANI-1"),
        CardDefinition("Fill", "Santo", "1", 1, 1, "", "ANI-1"),
    ]
    engine = GameEngine.create_new(cards, "P1", "P2", "ANI-1", "ANI-1", seed=126)
    _advance_to_active_phase(engine)
    while engine.state.active_player != 0:
        engine.end_turn()
        engine.start_turn()

    p1 = engine.state.players[1]
    rito_idx = _force_card_in_hand(engine, 0, "Rito Funebre")
    dead_uid = next(uid for uid in p1.deck if engine.state.instances[uid].definition.name == "DeadSaint")
    p1.deck.remove(dead_uid)
    p1.graveyard.append(dead_uid)
    out = engine.play_card(0, rito_idx, dead_uid)
    assert out.ok
    assert dead_uid not in p1.graveyard
    assert dead_uid in p1.deck


def test_rito_funebre_cannot_be_played_without_valid_graveyard_saint_targets() -> None:
    cards = [
        CardDefinition("Rito Funebre", "Benedizione", "1", None, None, "", "ANI-1"),
        CardDefinition("Fill", "Artefatto", "1", 1, None, "", "ANI-1"),
    ]
    engine = GameEngine.create_new(cards, "P1", "P2", "ANI-1", "ANI-1", seed=127)
    _advance_to_active_phase(engine)
    while engine.state.active_player != 0:
        engine.end_turn()
        engine.start_turn()
    idx = _force_card_in_hand(engine, 0, "Rito Funebre")
    out = engine.play_card(0, idx, None)
    assert not out.ok
    assert "nessun bersaglio valido disponibile" in out.message.lower()


def test_ritorno_catastrofico_is_scripted_and_returns_target_saint_to_owner_hand() -> None:
    script = runtime_cards.get_script("Ritorno Catastrofico")
    assert script is not None
    assert [a.effect.action for a in script.on_play_actions] == ["move_to_hand"]
    tgt = script.on_play_actions[0].target
    assert tgt.type == "selected_target"
    assert tgt.zone == "field"
    assert tgt.owner == "any"
    assert tgt.card_filter.card_type_in == ["santo"]
    assert tgt.min_targets == 1
    assert tgt.max_targets == 1

    cards = [
        CardDefinition("Ritorno Catastrofico", "Benedizione", "1", None, None, "", "NOR-1"),
        CardDefinition("MySaint", "Santo", "2", 3, 1, "", "NOR-1"),
        CardDefinition("Fill", "Santo", "1", 1, 1, "", "NOR-1"),
    ]
    engine = GameEngine.create_new(cards, "P1", "P2", "NOR-1", "NOR-1", seed=128)
    _advance_to_active_phase(engine)
    while engine.state.active_player != 0:
        engine.end_turn()
        engine.start_turn()

    p0 = engine.state.players[0]
    saint_idx = _force_card_in_hand(engine, 0, "MySaint")
    assert engine.play_card(0, saint_idx, "a1").ok
    target_uid = p0.attack[0]
    assert target_uid is not None

    spell_idx = _force_card_in_hand(engine, 0, "Ritorno Catastrofico")
    out = engine.play_card(0, spell_idx, "a1")
    assert out.ok
    assert p0.attack[0] is None
    assert target_uid in p0.hand


def test_ritorno_catastrofico_resets_runtime_stats_when_target_leaves_field() -> None:
    cards = [
        CardDefinition("Ritorno Catastrofico", "Benedizione", "1", None, None, "", "NOR-1"),
        CardDefinition("MySaint", "Santo", "2", 3, 1, "", "NOR-1"),
        CardDefinition("Fill", "Santo", "1", 1, 1, "", "NOR-1"),
    ]
    engine = GameEngine.create_new(cards, "P1", "P2", "NOR-1", "NOR-1", seed=131)
    _advance_to_active_phase(engine)
    while engine.state.active_player != 0:
        engine.end_turn()
        engine.start_turn()

    p0 = engine.state.players[0]
    saint_idx = _force_card_in_hand(engine, 0, "MySaint")
    assert engine.play_card(0, saint_idx, "a1").ok
    target_uid = p0.attack[0]
    assert target_uid is not None
    inst = engine.state.instances[target_uid]
    inst.current_faith = (inst.definition.faith or 0) + 7
    inst.blessed.append("buff_str:5")
    inst.cursed.append("silenced")
    inst.exhausted = True

    spell_idx = _force_card_in_hand(engine, 0, "Ritorno Catastrofico")
    out = engine.play_card(0, spell_idx, target_uid)
    assert out.ok
    assert target_uid in p0.hand
    assert inst.current_faith == inst.definition.faith
    assert inst.blessed == []
    assert inst.cursed == []
    assert inst.exhausted is False


def test_ritorno_catastrofico_can_target_opponent_saint_and_returns_to_opponent_hand() -> None:
    cards = [
        CardDefinition("Ritorno Catastrofico", "Benedizione", "1", None, None, "", "NOR-1"),
        CardDefinition("EnemySaint", "Santo", "2", 3, 1, "", "NOR-1"),
        CardDefinition("Fill", "Santo", "1", 1, 1, "", "NOR-1"),
    ]
    engine = GameEngine.create_new(cards, "P1", "P2", "NOR-1", "NOR-1", seed=130)
    _advance_to_active_phase(engine)
    while engine.state.active_player != 0:
        engine.end_turn()
        engine.start_turn()

    p0 = engine.state.players[0]
    p1 = engine.state.players[1]
    enemy_idx = _force_card_in_hand(engine, 1, "EnemySaint")
    enemy_uid = p1.hand.pop(enemy_idx)
    p1.attack[0] = enemy_uid
    assert enemy_uid is not None

    spell_idx = _force_card_in_hand(engine, 0, "Ritorno Catastrofico")
    out = engine.play_card(0, spell_idx, enemy_uid)
    assert out.ok
    assert p1.attack[0] is None
    assert enemy_uid in p1.hand
    assert enemy_uid not in p0.hand


def test_ritorno_catastrofico_cannot_be_played_without_own_saint_on_field() -> None:
    cards = [
        CardDefinition("Ritorno Catastrofico", "Benedizione", "1", None, None, "", "NOR-1"),
        CardDefinition("Fill", "Artefatto", "1", 1, None, "", "NOR-1"),
    ]
    engine = GameEngine.create_new(cards, "P1", "P2", "NOR-1", "NOR-1", seed=129)
    _advance_to_active_phase(engine)
    while engine.state.active_player != 0:
        engine.end_turn()
        engine.start_turn()
    idx = _force_card_in_hand(engine, 0, "Ritorno Catastrofico")
    out = engine.play_card(0, idx, None)
    assert not out.ok
    assert "nessun bersaglio valido disponibile" in out.message.lower()


def test_terremoto_magnitudo_10_is_scripted_with_vulcano_summon_and_self_excommunication() -> None:
    script = runtime_cards.get_script("Terremoto: Magnitudo 10")
    assert script is not None
    assert [a.effect.action for a in script.on_play_actions] == [
        "inflict_sin_to_target_owners",
        "send_to_graveyard",
        "summon_card_from_hand",
        "move_source_to_zone",
    ]


def test_terremoto_magnitudo_10_destroys_artifacts_buildings_adds_sin_and_summons_vulcano() -> None:
    cards = [
        CardDefinition("Terremoto: Magnitudo 10", "Maledizione", "1", None, None, "", "ANI-1"),
        CardDefinition("Vulcano", "Santo", "10", 25, 15, "", "ANI-1"),
        CardDefinition("P1Art", "Artefatto", "1", 1, None, "", "ANI-1"),
        CardDefinition("P1Bld", "Edificio", "1", 2, None, "", "ANI-1"),
        CardDefinition("P2Art", "Artefatto", "1", 1, None, "", "ANI-1"),
        CardDefinition("P2Bld", "Edificio", "1", 2, None, "", "ANI-1"),
        CardDefinition("Fill", "Santo", "1", 1, 1, "", "ANI-1"),
    ]
    engine = GameEngine.create_new(cards, "P1", "P2", "ANI-1", "ANI-1", seed=132)
    _advance_to_active_phase(engine)
    while engine.state.active_player != 0:
        engine.end_turn()
        engine.start_turn()

    p0 = engine.state.players[0]
    p1 = engine.state.players[1]

    mag_idx = _force_card_in_hand(engine, 0, "Terremoto: Magnitudo 10")
    mag_uid = p0.hand[mag_idx]
    vulcano_idx = _force_card_in_hand(engine, 0, "Vulcano")
    vulcano_uid = p0.hand[vulcano_idx]

    p1_art = next(uid for uid in p0.deck if engine.state.instances[uid].definition.name == "P1Art")
    p0.deck.remove(p1_art)
    p0.artifacts[0] = p1_art
    p1_bld = next(uid for uid in p0.deck if engine.state.instances[uid].definition.name == "P1Bld")
    p0.deck.remove(p1_bld)
    p0.building = p1_bld

    p2_art = next(uid for uid in p1.deck if engine.state.instances[uid].definition.name == "P2Art")
    p1.deck.remove(p2_art)
    p1.artifacts[0] = p2_art
    p2_bld = next(uid for uid in p1.deck if engine.state.instances[uid].definition.name == "P2Bld")
    p1.deck.remove(p2_bld)
    p1.building = p2_bld

    p0.sin = 0
    p1.sin = 0
    mag_idx = p0.hand.index(mag_uid)
    out = engine.play_card(0, mag_idx, None)
    assert out.ok

    assert p0.sin == 4
    assert p1.sin == 4

    assert p1_art in p0.graveyard
    assert p1_bld in p0.graveyard
    assert p2_art in p1.graveyard
    assert p2_bld in p1.graveyard
    assert p0.artifacts[0] is None
    assert p0.building is None
    assert p1.artifacts[0] is None
    assert p1.building is None

    assert vulcano_uid not in p0.hand
    assert vulcano_uid in p0.attack or vulcano_uid in p0.defense

    assert mag_uid in p0.excommunicated
    assert mag_uid not in p0.graveyard


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


def test_pietra_nera_equips_prevents_first_attack_then_goes_to_graveyard() -> None:
    cards = [
        CardDefinition("Pietra Nera", "Maledizione", "1", None, None, "", "ANI-1"),
        CardDefinition("Guardiano", "Santo", "2", 8, 1, "", "ANI-1"),
        CardDefinition("Assalitore", "Santo", "2", 8, 9, "", "ANI-1"),
    ]
    engine = GameEngine.create_new(cards, "P1", "P2", "ANI-1", "ANI-1", seed=141)
    _advance_to_active_phase(engine)
    while engine.state.active_player != 0:
        engine.end_turn()
        engine.start_turn()

    p0 = engine.state.players[0]
    p1 = engine.state.players[1]

    guard_idx = _force_card_in_hand(engine, 0, "Guardiano")
    assert engine.play_card(0, guard_idx, "a1").ok
    guard_uid = p0.attack[0]
    assert guard_uid is not None

    enemy_idx = _force_card_in_hand(engine, 1, "Assalitore")
    enemy_uid = p1.hand.pop(enemy_idx)
    p1.attack[0] = enemy_uid

    stone_idx = _force_card_in_hand(engine, 0, "Pietra Nera")
    stone_uid = p0.hand[stone_idx]
    out = engine.play_card(0, stone_idx, "a1")
    assert out.ok

    assert stone_uid in p0.artifacts
    assert f"equipped_to:{guard_uid}" in engine.state.instances[stone_uid].blessed
    assert f"equipped_by:{stone_uid}" in engine.state.instances[guard_uid].blessed

    guard_faith_before = int(engine.state.instances[guard_uid].current_faith or 0)

    engine.end_turn()
    engine.start_turn()
    assert engine.state.active_player == 1
    atk = engine.attack(1, 0, 0)
    assert atk.ok

    guard_faith_after = int(engine.state.instances[guard_uid].current_faith or 0)
    assert guard_faith_after == guard_faith_before
    assert stone_uid in p0.graveyard
    assert stone_uid not in p0.artifacts
    assert f"equipped_by:{stone_uid}" not in engine.state.instances[guard_uid].blessed


def test_pietra_nera_is_destroyed_when_equipped_target_leaves_field() -> None:
    cards = [
        CardDefinition("Pietra Nera", "Maledizione", "1", None, None, "", "ANI-1"),
        CardDefinition("Guardiano", "Santo", "2", 8, 1, "", "ANI-1"),
    ]
    engine = GameEngine.create_new(cards, "P1", "P2", "ANI-1", "ANI-1", seed=142)
    _advance_to_active_phase(engine)
    while engine.state.active_player != 0:
        engine.end_turn()
        engine.start_turn()

    p0 = engine.state.players[0]
    guard_idx = _force_card_in_hand(engine, 0, "Guardiano")
    assert engine.play_card(0, guard_idx, "a1").ok
    guard_uid = p0.attack[0]
    assert guard_uid is not None

    stone_idx = _force_card_in_hand(engine, 0, "Pietra Nera")
    stone_uid = p0.hand[stone_idx]
    out = engine.play_card(0, stone_idx, "a1")
    assert out.ok
    assert stone_uid in p0.artifacts

    engine.destroy_saint_by_uid(0, guard_uid, cause="effect")

    assert stone_uid in p0.graveyard
    assert stone_uid not in p0.artifacts


def test_pietre_pesanti_from_preparation_applies_only_on_first_real_opponent_turn() -> None:
    cards = [
        CardDefinition("Pietre Pesanti", "Maledizione", "1", None, None, "", "ANI-1"),
        CardDefinition("Bersaglio", "Santo", "4", 6, 2, "", "ANI-1"),
        CardDefinition("Fill", "Santo", "1", 1, 1, "", "ANI-1"),
    ]
    engine = GameEngine.create_new(cards, "P1", "P2", "ANI-1", "ANI-1", seed=143)

    # Preparation turn P1.
    assert engine.state.phase == "preparation"
    assert engine.state.active_player == 0
    engine.start_turn()
    p0 = engine.state.players[0]
    p1 = engine.state.players[1]

    heavy_idx = _force_card_in_hand(engine, 0, "Pietre Pesanti")
    out = engine.play_card(0, heavy_idx, None)
    assert out.ok
    assert int(engine.state.flags.setdefault("double_cost_next_turn", {"0": 0, "1": 0}).get("1", 0)) == 1

    engine.end_turn()

    # Preparation turn P2: effect must not be active yet.
    assert engine.state.active_player == 1
    assert engine.state.phase == "preparation"
    engine.start_turn()
    opp_idx_prep = _force_card_in_hand(engine, 1, "Bersaglio")
    opp_card_prep = engine.card_from_hand(1, opp_idx_prep)
    assert opp_card_prep is not None
    cost_prep = engine._calculate_play_cost(1, opp_idx_prep, opp_card_prep)
    assert cost_prep == int(opp_card_prep.definition.faith or 0)
    assert int(engine.state.flags.setdefault("double_cost_turns", {"0": 0, "1": 0}).get("1", 0)) == 0
    assert int(engine.state.flags.setdefault("double_cost_next_turn", {"0": 0, "1": 0}).get("1", 0)) == 1

    engine.end_turn()  # End preparation -> active phase starts.
    assert engine.state.phase == "active"

    # Reach P2 first real active turn.
    if engine.state.active_player != 1:
        engine.start_turn()
        engine.end_turn()
    assert engine.state.active_player == 1
    engine.start_turn()

    opp_idx_active = _force_card_in_hand(engine, 1, "Bersaglio")
    opp_card_active = engine.card_from_hand(1, opp_idx_active)
    assert opp_card_active is not None
    base_cost = int(opp_card_active.definition.faith or 0)
    cost_active = engine._calculate_play_cost(1, opp_idx_active, opp_card_active)
    assert cost_active == base_cost * 2
    assert int(engine.state.flags.setdefault("double_cost_next_turn", {"0": 0, "1": 0}).get("1", 0)) == 0

    engine.end_turn()

    # Next P2 active turn: the effect must be gone.
    engine.start_turn()
    engine.end_turn()
    assert engine.state.active_player == 1
    engine.start_turn()
    opp_idx_next = _force_card_in_hand(engine, 1, "Bersaglio")
    opp_card_next = engine.card_from_hand(1, opp_idx_next)
    assert opp_card_next is not None
    cost_next = engine._calculate_play_cost(1, opp_idx_next, opp_card_next)
    assert cost_next == base_cost


def test_memoria_della_pietra_does_not_target_pietra_bianca_blessing() -> None:
    cards = [
        CardDefinition("Memoria della Pietra", "Benedizione", "1", None, None, "", "ANI-1"),
        CardDefinition("Pietra Bianca", "Benedizione", "1", None, None, "", "ANI-1"),
        CardDefinition("Fill", "Santo", "1", 1, 1, "", "ANI-1"),
    ]
    engine = GameEngine.create_new(cards, "P1", "P2", "ANI-1", "ANI-1", seed=144)
    _advance_to_active_phase(engine)
    while engine.state.active_player != 0:
        engine.end_turn()
        engine.start_turn()

    p0 = engine.state.players[0]
    bianca_idx = _force_card_in_hand(engine, 0, "Pietra Bianca")
    bianca_uid = p0.hand.pop(bianca_idx)
    p0.graveyard.append(bianca_uid)

    memoria_idx = _force_card_in_hand(engine, 0, "Memoria della Pietra")
    out = engine.play_card(0, memoria_idx, "Pietra Bianca")
    assert not out.ok
    assert "nessun bersaglio valido disponibile" in out.message.lower()


def test_memoria_della_pietra_summons_only_pietra_saint_from_graveyard() -> None:
    cards = [
        CardDefinition("Memoria della Pietra", "Benedizione", "1", None, None, "", "ANI-1"),
        CardDefinition("Pietra Focaia", "Santo", "2", 5, 2, "", "ANI-1"),
        CardDefinition("Pietra Bianca", "Benedizione", "1", None, None, "", "ANI-1"),
        CardDefinition("Fill", "Santo", "1", 1, 1, "", "ANI-1"),
    ]
    engine = GameEngine.create_new(cards, "P1", "P2", "ANI-1", "ANI-1", seed=145)
    _advance_to_active_phase(engine)
    while engine.state.active_player != 0:
        engine.end_turn()
        engine.start_turn()

    p0 = engine.state.players[0]
    focaia_idx = _force_card_in_hand(engine, 0, "Pietra Focaia")
    focaia_uid = p0.hand.pop(focaia_idx)
    p0.graveyard.append(focaia_uid)
    bianca_idx = _force_card_in_hand(engine, 0, "Pietra Bianca")
    bianca_uid = p0.hand.pop(bianca_idx)
    p0.graveyard.append(bianca_uid)

    memoria_idx = _force_card_in_hand(engine, 0, "Memoria della Pietra")
    out = engine.play_card(0, memoria_idx, "Pietra Focaia")
    assert out.ok
    field_uids = [uid for uid in p0.attack + p0.defense if uid]
    field_names = [engine.state.instances[uid].definition.name for uid in field_uids]
    assert "Pietra Focaia" in field_names
    assert "Pietra Bianca" not in field_names
    assert bianca_uid in p0.graveyard


def test_pietre_aguzze_triggers_only_on_opponent_saint_entry() -> None:
    cards = [
        CardDefinition("Pietre Aguzze", "Artefatto", "1", 1, None, "", "ANI-1"),
        CardDefinition("MioSanto", "Santo", "2", 5, 2, "", "ANI-1"),
        CardDefinition("SantoNemico", "Santo", "2", 5, 2, "", "ANI-1"),
        CardDefinition("Fill", "Santo", "1", 1, 1, "", "ANI-1"),
    ]
    engine = GameEngine.create_new(cards, "P1", "P2", "ANI-1", "ANI-1", seed=146)
    _advance_to_active_phase(engine)
    while engine.state.active_player != 0:
        engine.end_turn()
        engine.start_turn()

    p0 = engine.state.players[0]
    p1 = engine.state.players[1]

    art_idx = _force_card_in_hand(engine, 0, "Pietre Aguzze")
    assert engine.play_card(0, art_idx, None).ok

    p0.sin = 0
    p1.sin = 0

    # Own saint entry must NOT trigger Pietre Aguzze.
    my_idx = _force_card_in_hand(engine, 0, "MioSanto")
    assert engine.play_card(0, my_idx, "a1").ok
    assert p0.sin == 0
    assert p1.sin == 0

    # Opponent saint entry MUST trigger once (+2 Sin to opponent).
    engine.end_turn()
    engine.start_turn()
    enemy_idx = _force_card_in_hand(engine, 1, "SantoNemico")
    assert engine.play_card(1, enemy_idx, "a1").ok
    assert p0.sin == 0
    assert p1.sin == 2


def test_defense_promotes_when_attack_leaves_field_to_hand_deck_or_excommunicated() -> None:
    cards = [
        CardDefinition("Front", "Santo", "2", 5, 2, "", "ANI-1"),
        CardDefinition("Back", "Santo", "2", 5, 2, "", "ANI-1"),
        CardDefinition("Fill", "Santo", "1", 1, 1, "", "ANI-1"),
    ]

    # to hand
    engine = GameEngine.create_new(cards, "P1", "P2", "ANI-1", "ANI-1", seed=147)
    _advance_to_active_phase(engine)
    while engine.state.active_player != 0:
        engine.end_turn()
        engine.start_turn()
    i_front = _force_card_in_hand(engine, 0, "Front")
    assert engine.play_card(0, i_front, "a1").ok
    i_back = _force_card_in_hand(engine, 0, "Back")
    assert engine.play_card(0, i_back, "d1").ok
    p0 = engine.state.players[0]
    front_uid = p0.attack[0]
    back_uid = p0.defense[0]
    assert front_uid and back_uid
    assert engine.move_board_card_to_hand(0, front_uid)
    assert p0.attack[0] == back_uid
    assert p0.defense[0] is None

    # to deck (relicario) via runtime move
    engine = GameEngine.create_new(cards, "P1", "P2", "ANI-1", "ANI-1", seed=148)
    _advance_to_active_phase(engine)
    while engine.state.active_player != 0:
        engine.end_turn()
        engine.start_turn()
    i_front = _force_card_in_hand(engine, 0, "Front")
    assert engine.play_card(0, i_front, "a1").ok
    i_back = _force_card_in_hand(engine, 0, "Back")
    assert engine.play_card(0, i_back, "d1").ok
    p0 = engine.state.players[0]
    front_uid = p0.attack[0]
    back_uid = p0.defense[0]
    assert front_uid and back_uid
    runtime_cards._move_uid_to_zone(engine, front_uid, "relicario", 0)  # noqa: SLF001 - regression test on runtime path
    assert p0.attack[0] == back_uid
    assert p0.defense[0] is None

    # to excommunicated
    engine = GameEngine.create_new(cards, "P1", "P2", "ANI-1", "ANI-1", seed=149)
    _advance_to_active_phase(engine)
    while engine.state.active_player != 0:
        engine.end_turn()
        engine.start_turn()
    i_front = _force_card_in_hand(engine, 0, "Front")
    assert engine.play_card(0, i_front, "a1").ok
    i_back = _force_card_in_hand(engine, 0, "Back")
    assert engine.play_card(0, i_back, "d1").ok
    p0 = engine.state.players[0]
    front_uid = p0.attack[0]
    back_uid = p0.defense[0]
    assert front_uid and back_uid
    engine.excommunicate_card(0, front_uid)
    assert p0.attack[0] == back_uid
    assert p0.defense[0] is None


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


def test_tempesta_is_marked_as_no_target_by_script_metadata() -> None:
    assert runtime_cards.get_play_targeting_mode("Tempesta") == "none"
    assert runtime_cards.get_play_targeting_mode("Figli di Odino") == "own_saint"
    assert runtime_cards.get_play_targeting_mode("Ricerca Archeologica") == "auto"
    assert runtime_cards.get_play_targeting_mode("Monsone") == "monsone"
    assert runtime_cards.get_play_targeting_mode("Brigante") == "none"
    assert runtime_cards.get_play_targeting_mode("Papa") == "none"
    assert runtime_cards.get_play_targeting_mode("Moribondo") == "own_saint"
    assert runtime_cards.get_play_targeting_mode("Arca della salvezza") == "manual"
    assert runtime_cards.get_attack_targeting_mode("Papa") == "only_if_no_other_attackers"
    assert runtime_cards.get_activate_targeting_mode("Yggdrasil") == "yggdrasil"
    assert runtime_cards.get_activate_targeting_mode("Vulcano") == "board_card"
    assert runtime_cards.get_play_targeting_mode("Missionario") == "none"
    assert runtime_cards.get_play_targeting_mode("Loki") == "none"
    assert runtime_cards.get_play_targeting_mode("Thor") == "none"
    assert runtime_cards.get_activate_targeting_mode("Tanngnjostr") == "none"
    assert runtime_cards.get_activate_targeting_mode("Tanngrisnir") == "none"
    assert runtime_cards.get_activate_targeting_mode("Paladino della Fede") == "auto"
    assert runtime_cards.get_play_owner("Missionario") == "opponent"
    assert runtime_cards.get_activate_targeting_mode("Loki") == "manual"
    assert runtime_cards.get_play_targeting_mode("Figli di Odino") == "own_saint"
    assert runtime_cards.get_play_targeting_mode("Tempesta di Asgard") == "none"


def test_yggdrasil_uses_scripted_enter_and_activate_modes() -> None:
    cards = [
        CardDefinition("Yggdrasil", "Edificio", "7", 6, None, "", "NOR-1"),
        CardDefinition("Thor", "Santo", "3", 1, 2, "", "NOR-1"),
        CardDefinition("Target", "Santo", "2", 1, 1, "", "NOR-1"),
    ]
    engine = GameEngine.create_new(cards, "P1", "P2", "NOR-1", "NOR-1", seed=14)
    _advance_to_active_phase(engine)
    while engine.state.active_player != 0:
        engine.end_turn()
        engine.start_turn()

    player = engine.state.players[0]
    thor_uid = next(
        uid
        for uid in (player.hand + player.deck)
        if engine.state.instances[uid].definition.name == "Thor"
    )
    if thor_uid in player.hand:
        player.hand.remove(thor_uid)
        player.deck.append(thor_uid)

    i_target = _force_card_in_hand(engine, 0, "Target")
    assert engine.play_card(0, i_target, "a1").ok
    target_uid = engine.state.players[0].attack[0]
    assert target_uid is not None

    i_ygg = _force_card_in_hand(engine, 0, "Yggdrasil")
    assert engine.play_card(0, i_ygg, None).ok
    hand_names = [engine.state.instances[uid].definition.name for uid in engine.state.players[0].hand]
    assert "Thor" in hand_names

    before_faith = engine.state.instances[target_uid].current_faith
    before_strength = engine.get_effective_strength(target_uid)
    ygg_uid = engine.state.players[0].building
    assert ygg_uid is not None
    assert engine.state.instances[ygg_uid].definition.name == "Yggdrasil"
    out = engine.activate_ability(0, "b", "buff:a1")
    assert out.ok
    assert engine.state.instances[target_uid].current_faith == (before_faith or 0) + 2
    assert engine.get_effective_strength(target_uid) == before_strength + 2


def test_albero_sacro_auto_enters_and_requests_end_turn() -> None:
    cards = [
        CardDefinition("Albero Sacro", "Santo", "7", 6, 5, "", "ANI-1"),
        CardDefinition("Token Albero", "Token", "1", 1, 0, "", "ANI-1"),
    ]
    engine = GameEngine.create_new(cards, "P1", "P2", "ANI-1", "ANI-1", seed=15)
    _advance_to_active_phase(engine)
    while engine.state.active_player != 0:
        engine.end_turn()
        engine.start_turn()
    player = engine.state.players[0]
    tree_uid = next(uid for uid in player.deck if engine.state.instances[uid].definition.name == "Albero Sacro")
    player.deck.remove(tree_uid)
    player.deck.append(tree_uid)
    active_before = engine.state.active_player
    engine.start_turn()
    assert engine.state.active_player != active_before
    assert any(
        uid and engine.state.instances[uid].definition.name == "Albero Sacro"
        for uid in player.attack + player.defense
    )


def test_vescovo_della_citta_buia_scales_with_enemy_saints() -> None:
    cards = [
        CardDefinition("Vescovo della Città Buia", "Santo", "8", 5, 5, "", "ANI-1"),
        CardDefinition("Enemy1", "Santo", "2", 2, 1, "", "ANI-1"),
        CardDefinition("Enemy2", "Santo", "2", 2, 1, "", "ANI-1"),
    ]
    engine = GameEngine.create_new(cards, "P1", "P2", "ANI-1", "ANI-1", seed=16)
    _advance_to_active_phase(engine)
    while engine.state.active_player != 0:
        engine.end_turn()
        engine.start_turn()
    p2 = engine.state.players[1]
    i1 = _force_card_in_hand(engine, 1, "Enemy1")
    assert engine.play_card(1, i1, "a1").ok
    i2 = _force_card_in_hand(engine, 1, "Enemy2")
    assert engine.play_card(1, i2, "a2").ok
    engine.end_turn()
    i_v = _force_card_in_hand(engine, 0, "Vescovo della Città Buia")
    assert engine.play_card(0, i_v, "a1").ok
    v_uid = engine.state.players[0].attack[0]
    assert v_uid is not None
    assert engine.state.instances[v_uid].current_faith == (engine.state.instances[v_uid].definition.faith or 0) + 10


def test_vescovo_della_citta_lucente_heals_damaged_saints() -> None:
    cards = [
        CardDefinition("Vescovo della Città Lucente", "Santo", "6", 7, 4, "", "ANI-1"),
        CardDefinition("Damaged", "Santo", "2", 3, 2, "", "ANI-1"),
    ]
    engine = GameEngine.create_new(cards, "P1", "P2", "ANI-1", "ANI-1", seed=17)
    _advance_to_active_phase(engine)
    while engine.state.active_player != 0:
        engine.end_turn()
        engine.start_turn()
    i_d = _force_card_in_hand(engine, 0, "Damaged")
    assert engine.play_card(0, i_d, "a1").ok
    d_uid = engine.state.players[0].attack[0]
    assert d_uid is not None
    engine.state.instances[d_uid].current_faith = 1
    i_v = _force_card_in_hand(engine, 0, "Vescovo della Città Lucente")
    assert engine.play_card(0, i_v, "a2").ok
    assert engine.state.instances[d_uid].current_faith == 6


def test_ah_puch_grows_when_token_or_saint_is_sent_from_field_to_graveyard() -> None:
    cards = [
        CardDefinition("Ah Puch", "Santo", "9", 7, 7, "", "MAY-1"),
        CardDefinition("Victim", "Santo", "2", 1, 1, "", "MAY-1"),
    ]
    engine = GameEngine.create_new(cards, "P1", "P2", "MAY-1", "MAY-1", seed=99)
    _advance_to_active_phase(engine)
    while engine.state.active_player != 0:
        engine.end_turn()
        engine.start_turn()

    i_ah = _force_card_in_hand(engine, 0, "Ah Puch")
    assert engine.play_card(0, i_ah, "a1").ok
    ah_uid = engine.state.players[0].attack[0]
    assert ah_uid is not None

    i_victim = _force_card_in_hand(engine, 0, "Victim")
    assert engine.play_card(0, i_victim, "a2").ok
    victim_uid = engine.state.players[0].attack[1]
    assert victim_uid is not None

    engine.send_to_graveyard(0, victim_uid)
    assert engine.state.instances[ah_uid].current_faith == 8
    assert engine.get_effective_strength(ah_uid) == 8


def test_fuoco_hits_only_saints_with_four_or_more_crosses() -> None:
    cards = [
        CardDefinition("Fuoco", "Artefatto", "1", 0, None, "", "CRI-1"),
        CardDefinition("Low", "Santo", "2", 2, 1, "", "CRI-1"),
        CardDefinition("High", "Santo", "4", 2, 1, "", "CRI-1"),
    ]
    engine = GameEngine.create_new(cards, "P1", "P2", "CRI-1", "CRI-1", seed=100)
    _advance_to_active_phase(engine)
    while engine.state.active_player != 0:
        engine.end_turn()
        engine.start_turn()

    i_fuoco = _force_card_in_hand(engine, 0, "Fuoco")
    assert engine.play_card(0, i_fuoco, None).ok
    i_low = _force_card_in_hand(engine, 0, "Low")
    assert engine.play_card(0, i_low, "a1").ok
    low_uid = engine.state.players[0].attack[0]
    assert low_uid is not None
    i_high = _force_card_in_hand(engine, 1, "High")
    engine.end_turn()
    assert engine.play_card(1, i_high, "a1").ok
    high_uid = engine.state.players[1].attack[0]
    assert high_uid is not None

    engine.state.instances[low_uid].current_faith = 2
    engine.state.instances[high_uid].current_faith = 2
    engine.end_turn()
    assert engine.state.players[0].attack[0] == low_uid
    assert engine.state.players[1].attack[0] is None
    assert low_uid in engine.state.instances


def test_terra_blocks_enemy_artifact_destruction() -> None:
    cards = [
        CardDefinition("Terra", "Artefatto", "1", 0, None, "", "CRI-1"),
        CardDefinition("Enemy Artifact", "Artefatto", "1", 0, None, "", "CRI-1"),
        CardDefinition("Target", "Santo", "2", 2, 2, "", "CRI-1"),
    ]
    engine = GameEngine.create_new(cards, "P1", "P2", "CRI-1", "CRI-1", seed=101)
    _advance_to_active_phase(engine)
    while engine.state.active_player != 0:
        engine.end_turn()
        engine.start_turn()

    i_terra = _force_card_in_hand(engine, 0, "Terra")
    assert engine.play_card(0, i_terra, None).ok
    i_target = _force_card_in_hand(engine, 0, "Target")
    assert engine.play_card(0, i_target, "a1").ok
    target_uid = engine.state.players[0].attack[0]
    assert target_uid is not None

    i_enemy_art = _force_card_in_hand(engine, 1, "Enemy Artifact")
    engine.end_turn()
    assert engine.play_card(1, i_enemy_art, None).ok
    enemy_art_uid = engine.state.players[1].artifacts[0]
    assert enemy_art_uid is not None

    engine.state.flags["_runtime_effect_source"] = enemy_art_uid
    engine.destroy_saint_by_uid(0, target_uid, cause="effect")
    assert engine.state.players[0].attack[0] == target_uid
    assert target_uid in engine.state.instances


def test_papa_attack_restriction_comes_from_script_metadata() -> None:
    cards = [
        CardDefinition("Papa", "Santo", "3", 5, 2, "", "CRI-1"),
        CardDefinition("Other", "Santo", "2", 2, 2, "", "CRI-1"),
        CardDefinition("Enemy", "Santo", "2", 2, 2, "", "CRI-1"),
    ]
    engine = GameEngine.create_new(cards, "P1", "P2", "CRI-1", "CRI-1", seed=102)
    _advance_to_active_phase(engine)
    while engine.state.active_player != 0:
        engine.end_turn()
        engine.start_turn()

    i_papa = _force_card_in_hand(engine, 0, "Papa")
    assert engine.play_card(0, i_papa, "a1").ok
    i_other = _force_card_in_hand(engine, 0, "Other")
    assert engine.play_card(0, i_other, "a2").ok
    i_enemy = _force_card_in_hand(engine, 1, "Enemy")
    engine.end_turn()
    assert engine.play_card(1, i_enemy, "a1").ok

    out = engine.attack(1, 0, 0)
    assert not out.ok
    assert "Papa" in out.message


def test_albero_fortunato_and_seguace_draw_on_death() -> None:
    cards = [
        CardDefinition("Albero Fortunato", "Santo", "2", 2, 1, "", "CRI-1"),
        CardDefinition("Seguace", "Santo", "1", 1, 1, "", "CRI-1"),
    ]
    engine = GameEngine.create_new(cards, "P1", "P2", "CRI-1", "CRI-1", seed=103)
    _advance_to_active_phase(engine)
    while engine.state.active_player != 0:
        engine.end_turn()
        engine.start_turn()

    i_tree = _force_card_in_hand(engine, 0, "Albero Fortunato")
    assert engine.play_card(0, i_tree, "a1").ok
    tree_uid = engine.state.players[0].attack[0]
    assert tree_uid is not None
    before = len(engine.state.players[0].hand)
    engine.destroy_saint_by_uid(0, tree_uid, cause="effect")
    assert len(engine.state.players[0].hand) == before + 2

    i_follow = _force_card_in_hand(engine, 0, "Seguace")
    assert engine.play_card(0, i_follow, "a1").ok
    follow_uid = engine.state.players[0].attack[0]
    assert follow_uid is not None
    before = len(engine.state.players[0].hand)
    engine.destroy_saint_by_uid(0, follow_uid, cause="effect")
    assert len(engine.state.players[0].hand) == before + 1


def test_neith_hits_all_opponent_saints_on_entry_against_defense_row() -> None:
    cards = [
        CardDefinition("Neith", "Santo", "3", 3, 2, "", "EGI-1"),
        CardDefinition("Enemy1", "Santo", "2", 2, 2, "", "EGI-1"),
        CardDefinition("Enemy2", "Santo", "2", 2, 2, "", "EGI-1"),
    ]
    engine = GameEngine.create_new(cards, "P1", "P2", "EGI-1", "EGI-1", seed=104)
    _advance_to_active_phase(engine)
    while engine.state.active_player != 0:
        engine.end_turn()
        engine.start_turn()
    engine.end_turn()
    i_e1 = _force_card_in_hand(engine, 1, "Enemy1")
    assert engine.play_card(1, i_e1, "a1").ok
    i_e2 = _force_card_in_hand(engine, 1, "Enemy2")
    assert engine.play_card(1, i_e2, "a2").ok
    e1_uid = engine.state.players[1].attack[0]
    e2_uid = engine.state.players[1].attack[1]
    assert e1_uid and e2_uid
    engine.end_turn()
    i_neith = _force_card_in_hand(engine, 0, "Neith")
    assert engine.play_card(0, i_neith, "a1").ok
    assert engine.state.instances[e1_uid].current_faith == 1
    assert engine.state.instances[e2_uid].current_faith == 1


def test_araldo_and_custode_manage_sigilli_via_script() -> None:
    cards = [
        CardDefinition("Altare dei Sette Sigilli", "Edificio", "1", 0, None, "", "CRI-1"),
        CardDefinition("Araldo della Fine", "Santo", "7", 5, 4, "", "CRI-1"),
        CardDefinition("Custode dei Sigilli", "Santo", "4", 4, 3, "", "CRI-1"),
    ]
    engine = GameEngine.create_new(cards, "P1", "P2", "CRI-1", "CRI-1", seed=105)
    _advance_to_active_phase(engine)
    while engine.state.active_player != 0:
        engine.end_turn()
        engine.start_turn()
    i_altare = _force_card_in_hand(engine, 0, "Altare dei Sette Sigilli")
    assert engine.play_card(0, i_altare, None).ok

    engine._set_altare_sigilli(0, 6)
    i_custode = _force_card_in_hand(engine, 0, "Custode dei Sigilli")
    assert engine.play_card(0, i_custode, "a1").ok
    custode_uid = engine.state.players[0].attack[0]
    assert custode_uid is not None
    assert (engine.state.instances[custode_uid].current_faith or 0) >= 6
    assert engine.get_effective_strength(custode_uid) >= 6

    i_araldo = _force_card_in_hand(engine, 0, "Araldo della Fine")
    assert engine.play_card(0, i_araldo, "a2").ok
    araldo_uid = engine.state.players[0].attack[1]
    assert araldo_uid is not None
    before = engine._get_altare_sigilli(0)
    engine.destroy_saint_by_uid(0, araldo_uid, cause="effect")
    assert engine._get_altare_sigilli(0) >= before + 3


def test_neith_hits_all_opponent_saints_on_entry() -> None:
    cards = [
        CardDefinition("Neith", "Santo", "3", 3, 2, "", "EGI-1"),
        CardDefinition("Enemy1", "Santo", "2", 2, 2, "", "EGI-1"),
        CardDefinition("Enemy2", "Santo", "2", 2, 2, "", "EGI-1"),
    ]
    engine = GameEngine.create_new(cards, "P1", "P2", "EGI-1", "EGI-1", seed=104)
    _advance_to_active_phase(engine)
    while engine.state.active_player != 0:
        engine.end_turn()
        engine.start_turn()
    engine.end_turn()
    i_e1 = _force_card_in_hand(engine, 1, "Enemy1")
    assert engine.play_card(1, i_e1, "a1").ok
    i_e2 = _force_card_in_hand(engine, 1, "Enemy2")
    assert engine.play_card(1, i_e2, "a2").ok
    e1_uid = engine.state.players[1].attack[0]
    e2_uid = engine.state.players[1].attack[1]
    assert e1_uid and e2_uid
    engine.end_turn()
    i_neith = _force_card_in_hand(engine, 0, "Neith")
    assert engine.play_card(0, i_neith, "a1").ok
    assert engine.state.instances[e1_uid].current_faith == 1
    assert engine.state.instances[e2_uid].current_faith == 1


def test_spirito_dei_sepolti_buffs_all_other_saints_on_leave() -> None:
    cards = [
        CardDefinition("Spirito dei Sepolti", "Santo", "4", 4, 3, "", "MAY-1"),
        CardDefinition("Friend", "Santo", "2", 2, 2, "", "MAY-1"),
    ]
    engine = GameEngine.create_new(cards, "P1", "P2", "MAY-1", "MAY-1", seed=107)
    _advance_to_active_phase(engine)
    while engine.state.active_player != 0:
        engine.end_turn()
        engine.start_turn()
    i_sp = _force_card_in_hand(engine, 0, "Spirito dei Sepolti")
    assert engine.play_card(0, i_sp, "a1").ok
    sp_uid = engine.state.players[0].attack[0]
    assert sp_uid is not None
    i_friend = _force_card_in_hand(engine, 0, "Friend")
    assert engine.play_card(0, i_friend, "a2").ok
    friend_uid = engine.state.players[0].attack[1]
    assert friend_uid is not None
    engine.destroy_saint_by_uid(0, sp_uid, cause="effect")
    assert engine.state.instances[friend_uid].current_faith == 3
    assert engine.get_effective_strength(friend_uid) == 4


def test_fujn_dar_mills_two_cards_after_battle_kill() -> None:
    cards = [
        CardDefinition("Fujn-dar", "Santo", "6", 4, 4, "", "PHD-1"),
        CardDefinition("Victim", "Santo", "2", 2, 2, "", "PHD-1"),
    ]
    engine = GameEngine.create_new(cards, "P1", "P2", "PHD-1", "PHD-1", seed=108)
    _advance_to_active_phase(engine)
    while engine.state.active_player != 0:
        engine.end_turn()
        engine.start_turn()
    i_att = _force_card_in_hand(engine, 0, "Fujn-dar")
    assert engine.play_card(0, i_att, "a1").ok
    engine.end_turn()
    i_def = _force_card_in_hand(engine, 1, "Victim")
    assert engine.play_card(1, i_def, "a1").ok
    victim_hand_before = len(engine.state.players[1].hand)
    engine.end_turn()
    engine.start_turn()
    out = engine.attack(0, 0, 0)
    assert out.ok
    assert len(engine.state.players[1].hand) == victim_hand_before - 2


def test_loki_sacrifices_self_to_summon_from_hand() -> None:
    cards = [
        CardDefinition("Loki", "Santo", "6", 6, 2, "", "NOR-1"),
        CardDefinition("Fenrir", "Santo", "3", 4, 4, "", "NOR-1"),
        CardDefinition("Jormungandr", "Santo", "10", 25, 6, "", "NOR-1"),
    ]
    engine = GameEngine.create_new(cards, "P1", "P2", "NOR-1", "NOR-1", seed=110)
    _advance_to_active_phase(engine)
    while engine.state.active_player != 0:
        engine.end_turn()
        engine.start_turn()
    i_loki = _force_card_in_hand(engine, 0, "Loki")
    assert engine.play_card(0, i_loki, "a1").ok
    out = engine.activate_ability(0, "a1", "Fenrir")
    assert out.ok
    assert any(engine.state.instances[uid].definition.name == "Loki" for uid in engine.state.players[0].graveyard)
    assert any(
        uid is not None and engine.state.instances[uid].definition.name == "Fenrir"
        for uid in engine.state.players[0].attack
    )


def test_aquila_vorace_returns_to_hand_again_after_replay_on_later_turn() -> None:
    cards = [
        CardDefinition("Aquila Vorace", "Santo", "6", 2, 8, "", "ANI-1"),
        CardDefinition("Victim1", "Santo", "2", 2, 1, "", "ANI-1"),
        CardDefinition("Victim2", "Santo", "2", 2, 1, "", "ANI-1"),
    ]
    engine = GameEngine.create_new(cards, "P1", "P2", "ANI-1", "ANI-1", seed=116)
    _advance_to_active_phase(engine)
    while engine.state.active_player != 0:
        engine.end_turn()
        engine.start_turn()

    p0 = engine.state.players[0]
    p1 = engine.state.players[1]

    idx_a = _force_card_in_hand(engine, 0, "Aquila Vorace")
    uid_a = p0.hand[idx_a]
    for uid in list(p0.hand):
        if uid != uid_a:
            p0.hand.remove(uid)
            p0.deck.append(uid)
    idx_a = p0.hand.index(uid_a)
    assert engine.play_card(0, idx_a, "a1").ok

    idx_v1 = _force_card_in_hand(engine, 1, "Victim1")
    assert engine.play_card(1, idx_v1, "a1").ok
    engine.end_turn()
    engine.start_turn()
    out = engine.attack(0, 0, 0)
    assert out.ok
    assert uid_a in p0.hand
    assert p0.attack[0] is None

    engine.end_turn()
    engine.start_turn()
    engine.end_turn()
    engine.start_turn()

    idx_a2 = p0.hand.index(uid_a)
    assert engine.play_card(0, idx_a2, "a1").ok
    idx_v2 = _force_card_in_hand(engine, 1, "Victim2")
    assert engine.play_card(1, idx_v2, "a1").ok
    engine.end_turn()
    engine.start_turn()
    out2 = engine.attack(0, 0, 0)
    assert out2.ok
    assert uid_a in p0.hand
    assert p0.attack[0] is None


def test_tanng_cards_activate_scripted_sacrifice_to_buff_thor() -> None:
    cards = [
        CardDefinition("Thor", "Santo", "9", 10, 8, "", "NOR-1"),
        CardDefinition("Tanngnjostr", "Santo", "2", 2, 3, "", "NOR-1"),
        CardDefinition("Tanngrisnir", "Santo", "2", 2, 3, "", "NOR-1"),
    ]
    engine = GameEngine.create_new(cards, "P1", "P2", "NOR-1", "NOR-1", seed=111)
    _advance_to_active_phase(engine)
    while engine.state.active_player != 0:
        engine.end_turn()
        engine.start_turn()
    engine.state.players[0].inspiration = 30
    i_thor = _force_card_in_hand(engine, 0, "Thor")
    assert engine.play_card(0, i_thor, "a1").ok
    i_t1 = _force_card_in_hand(engine, 0, "Tanngnjostr")
    assert engine.play_card(0, i_t1, "a2").ok
    thor_uid = engine.state.players[0].attack[0]
    assert thor_uid is not None
    before = engine.state.instances[thor_uid].current_faith or 0
    out = engine.activate_ability(0, "a2", None)
    assert out.ok
    assert engine.state.instances[thor_uid].current_faith == before + 4
    assert engine.state.players[0].attack[1] is None
    assert any(engine.state.instances[uid].definition.name == "Tanngnjostr" for uid in engine.state.players[0].graveyard)


def test_albero_sconsacrato_grants_inspiration_on_own_turn_start() -> None:
    cards = [
        CardDefinition("Albero Sconsacrato", "Santo", "3", 3, 0, "", "ANI-1"),
    ]
    engine = GameEngine.create_new(cards, "P1", "P2", "ANI-1", "ANI-1", seed=112)
    _advance_to_active_phase(engine)
    while engine.state.active_player != 0:
        engine.end_turn()
        engine.start_turn()
    idx = _force_card_in_hand(engine, 0, "Albero Sconsacrato")
    assert engine.play_card(0, idx, "a1").ok
    before = engine.state.players[0].inspiration
    engine.end_turn()
    engine.start_turn()
    engine.end_turn()
    engine.start_turn()
    assert engine.state.players[0].inspiration >= before + 2


def test_paladino_della_fede_swaps_one_own_saint_between_attack_and_defense() -> None:
    cards = [
        CardDefinition("Paladino della Fede", "Santo", "4", 4, 3, "", "CRI-1"),
        CardDefinition("Friend A", "Santo", "2", 2, 2, "", "CRI-1"),
        CardDefinition("Friend D", "Santo", "2", 2, 2, "", "CRI-1"),
    ]
    engine = GameEngine.create_new(cards, "P1", "P2", "CRI-1", "CRI-1", seed=113)
    _advance_to_active_phase(engine)
    while engine.state.active_player != 0:
        engine.end_turn()
        engine.start_turn()
    idx_a = _force_card_in_hand(engine, 0, "Friend A")
    assert engine.play_card(0, idx_a, "a2").ok
    idx_d = _force_card_in_hand(engine, 0, "Friend D")
    assert engine.play_card(0, idx_d, "d1").ok
    idx = _force_card_in_hand(engine, 0, "Paladino della Fede")
    assert engine.play_card(0, idx, "a1").ok
    assert engine.state.players[0].attack[0] is not None
    assert engine.state.players[0].defense[0] is not None
    before_attack = engine.state.instances[engine.state.players[0].attack[0]].definition.name
    before_defense = engine.state.instances[engine.state.players[0].defense[0]].definition.name
    assert before_attack == "Friend D"
    assert before_defense == "Paladino della Fede"
    after_attack = engine.state.instances[engine.state.players[0].attack[0]].definition.name
    after_defense = engine.state.instances[engine.state.players[0].defense[0]].definition.name
    assert after_attack == "Friend D"
    assert after_defense == "Paladino della Fede"


def test_prete_anziano_removes_three_sin_on_attack() -> None:
    cards = [
        CardDefinition("Prete Anziano", "Santo", "1", 1, 3, "", "ANI-1"),
        CardDefinition("Enemy", "Santo", "2", 3, 1, "", "ANI-1"),
    ]
    engine = GameEngine.create_new(cards, "P1", "P2", "ANI-1", "ANI-1", seed=114)
    _advance_to_active_phase(engine)
    while engine.state.active_player != 0:
        engine.end_turn()
        engine.start_turn()
    i1 = _force_card_in_hand(engine, 0, "Prete Anziano")
    assert engine.play_card(0, i1, "a1").ok
    i2 = _force_card_in_hand(engine, 1, "Enemy")
    engine.end_turn()
    engine.start_turn()
    assert engine.play_card(1, i2, "a1").ok
    engine.end_turn()
    engine.start_turn()
    engine.state.players[0].sin = 5
    before = engine.state.players[0].sin
    out = engine.attack(0, 0, 0)
    assert out.ok
    assert engine.state.players[0].sin == before - 3


def test_missionario_returns_to_relicario_after_effect_death() -> None:
    cards = [
        CardDefinition("Missionario", "Santo", "5", 6, 0, "", "ANI-1"),
    ]
    engine = GameEngine.create_new(cards, "P1", "P2", "ANI-1", "ANI-1", seed=115)
    _advance_to_active_phase(engine)
    while engine.state.active_player != 0:
        engine.end_turn()
        engine.start_turn()
    idx = _force_card_in_hand(engine, 0, "Missionario")
    assert engine.play_card(0, idx, "a1").ok
    uid = engine.state.players[1].attack[0]
    assert uid is not None
    engine.state.instances[uid].current_faith = 6
    engine.end_turn()
    assert engine.state.instances[uid].current_faith == 3
    engine.end_turn()
    assert uid in engine.state.players[0].deck
    assert uid not in engine.state.players[0].graveyard


def test_ptah_can_return_a_drawn_card_to_relicario() -> None:
    cards = [
        CardDefinition("Ptah", "Santo", "3", 3, 2, "", "EGI-1"),
        CardDefinition("Drawn", "Santo", "1", 1, 1, "", "EGI-1"),
        CardDefinition("Replacement", "Santo", "1", 1, 1, "", "EGI-1"),
    ]
    engine = GameEngine.create_new(cards, "P1", "P2", "EGI-1", "EGI-1", seed=116)
    _advance_to_active_phase(engine)
    while engine.state.active_player != 0:
        engine.end_turn()
        engine.start_turn()
    p0 = engine.state.players[0]
    ptah_idx = _force_card_in_hand(engine, 0, "Ptah")
    ptah_uid = p0.hand[ptah_idx]
    assert engine.play_card(0, ptah_idx, "a1").ok
    drawn_uid = next(uid for uid in p0.hand if engine.state.instances[uid].definition.name == "Drawn")
    replacement_uid = next(uid for uid in p0.deck if engine.state.instances[uid].definition.name == "Replacement")
    p0.hand = [drawn_uid]
    p0.deck = [replacement_uid]
    engine.state.flags.setdefault("cards_drawn_this_turn", {"0": [], "1": []})["0"] = [drawn_uid]
    targets = runtime_cards._resolve_targets(  # noqa: SLF001 - targeted regression for Ptah primitive
        engine,
        0,
        TargetSpec(
            type="cards_controlled_by_owner",
            card_filter=CardFilterSpec(drawn_this_turn_only=True),
            zone="hand",
            owner="me",
            max_targets=1,
        ),
    )
    assert targets == [drawn_uid]
    ptah_script = runtime_cards.get_script("Ptah")
    assert ptah_script is not None
    runtime_cards._apply_effect(engine, 0, ptah_uid, targets, ptah_script.triggered_effects[0].effect)  # noqa: SLF001
    assert drawn_uid in p0.deck
    assert drawn_uid not in p0.hand


def test_tikal_is_scripted_with_deck_bottom_and_moves_top_cards_correctly() -> None:
    script = runtime_cards.get_script("Tikal")
    assert script is not None
    assert script.activate_targeting == "none"
    assert script.activate_once_per_turn is True
    assert [a.effect.action for a in script.on_activate_actions] == [
        "store_top_card_of_zone",
        "reveal_stored_card",
        "move_stored_card_to_zone",
        "move_stored_card_to_zone",
    ]

    saint_cards = [
        CardDefinition("Tikal", "Edificio", "1", 1, None, "", "MAY-1"),
        CardDefinition("TopSaint", "Santo", "1", 1, 1, "", "MAY-1"),
        CardDefinition("Fill", "Santo", "1", 1, 1, "", "MAY-1"),
    ]
    engine = GameEngine.create_new(saint_cards, "P1", "P2", "MAY-1", "MAY-1", seed=118)
    _advance_to_active_phase(engine)
    while engine.state.active_player != 0:
        engine.end_turn()
        engine.start_turn()
    p0 = engine.state.players[0]
    tikal_idx = _force_card_in_hand(engine, 0, "Tikal")
    assert engine.play_card(0, tikal_idx, None).ok
    top_saint_uid = next(uid for uid in p0.deck if engine.state.instances[uid].definition.name == "TopSaint")
    p0.deck = [top_saint_uid]
    assert engine.activate_ability(0, "b", None).ok
    assert top_saint_uid in p0.hand
    assert top_saint_uid not in p0.deck
    assert not engine.activate_ability(0, "b", None).ok

    spell_cards = [
        CardDefinition("Tikal", "Edificio", "1", 1, None, "", "MAY-1"),
        CardDefinition("TopSpell", "Benedizione", "1", None, None, "", "MAY-1"),
        CardDefinition("Fill", "Santo", "1", 1, 1, "", "MAY-1"),
    ]
    engine = GameEngine.create_new(spell_cards, "P1", "P2", "MAY-1", "MAY-1", seed=119)
    _advance_to_active_phase(engine)
    while engine.state.active_player != 0:
        engine.end_turn()
        engine.start_turn()
    p0 = engine.state.players[0]
    tikal_idx = _force_card_in_hand(engine, 0, "Tikal")
    assert engine.play_card(0, tikal_idx, None).ok
    top_spell_uid = next(uid for uid in p0.deck if engine.state.instances[uid].definition.name == "TopSpell")
    filler_uid = next(uid for uid in p0.deck if uid != top_spell_uid)
    p0.deck = [filler_uid, top_spell_uid]
    assert engine.activate_ability(0, "b", None).ok
    assert top_spell_uid not in p0.hand
    assert p0.deck[0] == top_spell_uid

    cap_cards = [
        CardDefinition("Tikal", "Edificio", "1", 1, None, "", "MAY-1"),
        CardDefinition("TopSaint", "Santo", "1", 1, 1, "", "MAY-1"),
        CardDefinition("Fill1", "Santo", "1", 1, 1, "", "MAY-1"),
        CardDefinition("Fill2", "Santo", "1", 1, 1, "", "MAY-1"),
        CardDefinition("Fill3", "Santo", "1", 1, 1, "", "MAY-1"),
        CardDefinition("Fill4", "Santo", "1", 1, 1, "", "MAY-1"),
    ]
    engine = GameEngine.create_new(cap_cards, "P1", "P2", "MAY-1", "MAY-1", seed=120)
    _advance_to_active_phase(engine)
    while engine.state.active_player != 0:
        engine.end_turn()
        engine.start_turn()
    p0 = engine.state.players[0]
    tikal_idx = _force_card_in_hand(engine, 0, "Tikal")
    assert engine.play_card(0, tikal_idx, None).ok
    top_saint_uid = next(uid for uid in p0.deck if engine.state.instances[uid].definition.name == "TopSaint")
    extra_uids = [uid for uid in p0.deck if uid != top_saint_uid][:3]
    for uid in extra_uids:
        p0.deck.remove(uid)
        p0.hand.append(uid)
    p0.deck = [top_saint_uid]
    assert len(p0.hand) == 8
    assert engine.activate_ability(0, "b", None).ok
    assert len(p0.hand) == 8
    assert top_saint_uid in p0.deck


def test_deriu_hebet_is_scripted_with_shuffle_and_draws_blessings() -> None:
    script = runtime_cards.get_script("Deriu-hebet")
    assert script is not None
    assert script.activate_targeting == "none"
    assert script.activate_once_per_turn is True
    assert [a.effect.action for a in script.on_activate_actions] == [
        "store_top_card_of_zone",
        "reveal_stored_card",
        "move_stored_card_to_zone",
        "shuffle_deck",
    ]

    cards = [
        CardDefinition("Deriu-hebet", "Santo", "1", 3, 1, "", "EGI-1"),
        CardDefinition("BlessX", "Benedizione", "1", None, None, "", "EGI-1"),
        CardDefinition("Fill", "Santo", "1", 1, 1, "", "EGI-1"),
    ]
    engine = GameEngine.create_new(cards, "P1", "P2", "EGI-1", "EGI-1", seed=119)
    _advance_to_active_phase(engine)
    while engine.state.active_player != 0:
        engine.end_turn()
        engine.start_turn()
    p0 = engine.state.players[0]
    deriu_idx = _force_card_in_hand(engine, 0, "Deriu-hebet")
    assert engine.play_card(0, deriu_idx, "a1").ok

    bless_uid = next(uid for uid in p0.deck if engine.state.instances[uid].definition.name == "BlessX")
    p0.deck = [bless_uid]
    assert engine.activate_ability(0, "a1", None).ok
    assert bless_uid in p0.hand
    assert bless_uid not in p0.deck
    assert not engine.activate_ability(0, "a1", None).ok


def test_sif_is_scripted_activate_once_per_turn_and_buffs_own_saint() -> None:
    script = runtime_cards.get_script("Sif")
    assert script is not None
    assert script.on_activate_mode == "scripted"
    assert script.activate_once_per_turn is True
    assert script.activate_targeting == "board_card"
    assert [a.effect.action for a in script.on_activate_actions] == ["increase_faith"]

    cards = [
        CardDefinition("Sif", "Santo", "4", 4, 2, "", "NOR-1"),
        CardDefinition("Thor", "Santo", "4", 6, 3, "", "NOR-1"),
    ]
    engine = GameEngine.create_new(cards, "P1", "P2", "NOR-1", "NOR-1", seed=130)
    _advance_to_active_phase(engine)
    while engine.state.active_player != 0:
        engine.end_turn()
        engine.start_turn()

    p0 = engine.state.players[0]
    sif_idx = _force_card_in_hand(engine, 0, "Sif")
    assert engine.play_card(0, sif_idx, "a1").ok
    thor_idx = _force_card_in_hand(engine, 0, "Thor")
    assert engine.play_card(0, thor_idx, "a2").ok

    thor_uid = p0.attack[1]
    assert thor_uid is not None
    before_faith = engine.state.instances[thor_uid].current_faith

    out1 = engine.activate_ability(0, "a1", "a2")
    out2 = engine.activate_ability(0, "a1", "a2")
    assert out1.ok
    assert out2.ok
    assert "gia usata" in out2.message.lower()
    assert engine.state.instances[thor_uid].current_faith == (before_faith or 0) + 4


def test_playing_radici_does_not_log_literal_none() -> None:
    cards = [
        CardDefinition("Radici", "Artefatto", "1", 1, None, "", "ANI-1"),
        CardDefinition("Fill", "Santo", "1", 1, 1, "", "ANI-1"),
    ]
    engine = GameEngine.create_new(cards, "P1", "P2", "ANI-1", "ANI-1", seed=125)
    _advance_to_active_phase(engine)
    while engine.state.active_player != 0:
        engine.end_turn()
        engine.start_turn()
    idx = _force_card_in_hand(engine, 0, "Radici")
    out = engine.play_card(0, idx, None)
    assert out.ok
    assert all(str(line).strip().lower() != "none" for line in engine.state.logs)


def test_veggente_searches_sigillo_and_uses_altar_script() -> None:
    cards = [
        CardDefinition("Veggente dell'Apocalisse", "Santo", "7", 8, 3, "", "ANI-1"),
        CardDefinition("Altare dei Sette Sigilli", "Edificio", "7", 6, None, "", "ANI-1"),
        CardDefinition("Primo Sigillo", "Benedizione", "1", 0, 0, "", "ANI-1"),
    ]
    engine = GameEngine.create_new(cards, "P1", "P2", "ANI-1", "ANI-1", seed=117)
    _advance_to_active_phase(engine)
    while engine.state.active_player != 0:
        engine.end_turn()
        engine.start_turn()
    p0 = engine.state.players[0]
    altar_idx = _force_card_in_hand(engine, 0, "Altare dei Sette Sigilli")
    assert engine.play_card(0, altar_idx, None).ok
    p0.inspiration = 20
    veg_idx = _force_card_in_hand(engine, 0, "Veggente dell'Apocalisse")
    assert engine.play_card(0, veg_idx, "a1").ok
    assert any(engine.state.instances[uid].definition.name == "Primo Sigillo" for uid in p0.hand)
    p0.inspiration = 20
    engine._set_altare_sigilli(0, 0)
    out_add = engine.activate_ability(0, "a1", "add")
    assert out_add.ok
    assert engine._get_altare_sigilli(0) == 1
    engine._set_altare_sigilli(0, 3)
    before_hand = len(p0.hand)
    out = engine.activate_ability(0, "a1", "draw")
    assert out.ok
    assert engine._get_altare_sigilli(0) == 0
    assert len(p0.hand) == before_hand + 1

from __future__ import annotations

from holywar.data.deck_builder import available_premade_decks, build_premade_deck
from holywar.data.models import CardDefinition


def test_available_premade_has_expected_decks() -> None:
    decks = available_premade_decks("Animismo")
    ids = {d[0] for d in decks}
    assert "animismo_b1_antico_albero" in ids


def test_build_premade_falls_back_to_45_cards() -> None:
    cards = [
        CardDefinition("Albero Sacro", "Santo", "White", 10, 0, "", "ANI-1"),
        CardDefinition("Ruscello Sacro", "Edificio", "8", 8, None, "", "ANI-1"),
        CardDefinition("Cuore della foresta", "Artefatto", "5", 5, None, "", "ANI-1"),
        CardDefinition("Corteccia", "Artefatto", "5", 5, None, "", "ANI-1"),
        CardDefinition("Radici", "Artefatto", "6", 6, None, "", "ANI-1"),
        CardDefinition("Preghiera: Fertilita", "Benedizione", "7", None, None, "", "ANI-1"),
        CardDefinition("Albero Fortunato", "Santo", "2", 2, 1, "", "ANI-1"),
        CardDefinition("Albero Secolare", "Santo", "7", 7, 3, "", "ANI-1"),
        CardDefinition("Foresta Sacra", "Edificio", "10", 10, None, "", "ANI-1"),
        CardDefinition("Pioggia", "Benedizione", "3", None, None, "", "ANI-1"),
        CardDefinition("Barriera Magica", "Benedizione", "1", None, None, "", "NEU-1"),
        CardDefinition("Concentrazione", "Benedizione", "3", None, None, "", "NEU-1"),
        CardDefinition("Meditazione", "Benedizione", "2", None, None, "", "NEU-1"),
        CardDefinition("Cura", "Benedizione", "3", None, None, "", "NEU-1"),
        CardDefinition("Cura Rapida", "Benedizione", "3", None, None, "", "NEU-1"),
        CardDefinition("Seguace", "Santo", "2", 5, 2, "", "NEU-1"),
        CardDefinition("Moribondo", "Santo", "2", 1, 1, "", "NEU-1"),
        CardDefinition("Ricerca Archeologica", "Benedizione", "2", None, None, "", "NEU-1"),
        CardDefinition("Rinforzi", "Benedizione", "2", None, None, "", "NEU-1"),
    ]

    built = build_premade_deck(cards, "animismo_b1_antico_albero")
    assert len(built.deck.main_deck) == 45

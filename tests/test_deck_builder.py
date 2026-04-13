from __future__ import annotations

from holywar.data.deck_builder import build_test_deck
from holywar.data.models import CardDefinition


def _card(name: str, ctype: str, crosses: str, expansion: str, faith: int | None = 1, strength: int | None = 1):
    return CardDefinition(name, ctype, crosses, faith, strength, "", expansion)


def test_build_test_deck_has_fixed_size_and_tokens() -> None:
    cards = [
        _card("S1", "Santo", "2", "Animismo", 2, 2),
        _card("S2", "Santo", "3", "Animismo", 2, 2),
        _card("S3", "Santo", "4", "Animismo", 2, 2),
        _card("S4", "Santo", "5", "Animismo", 2, 2),
        _card("S5", "Santo", "6", "Animismo", 2, 2),
        _card("B1", "Benedizione", "2", "Animismo", None, None),
        _card("M1", "Maledizione", "2", "Animismo", None, None),
        _card("N1", "Benedizione", "2", "NEU-1", None, None),
        _card("Tok", "Token", "1", "Animismo", 1, 1),
    ]
    deck = build_test_deck(cards, "Animismo")
    assert len(deck.main_deck) == 45
    assert len(deck.white_deck) == 5
    assert all(c.card_type.lower() != "token" for c in deck.main_deck)


def test_build_test_deck_respects_cross_band_caps() -> None:
    cards = [
        _card(f"H{i}", "Santo", "8", "Animismo", 2, 2)
        for i in range(20)
    ] + [
        _card(f"L{i}", "Santo", "2", "Animismo", 2, 2)
        for i in range(7)
    ]

    deck = build_test_deck(cards, "Animismo")
    high_count = sum(1 for c in deck.main_deck if c.crosses == "8")
    assert high_count <= 10
    assert len(deck.main_deck) == 45

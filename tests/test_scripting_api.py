from __future__ import annotations

from holywar.core.engine import GameEngine
from holywar.data.models import CardDefinition
from holywar.scripting_api import DECLARED_FUNCTIONS, RuleEvents


def test_rules_api_exposes_declared_surface() -> None:
    cards = [CardDefinition("S", "Santo", "2", 1, 1, "", "NEU-1")]
    engine = GameEngine.create_new(cards, "P1", "P2", "NEU-1", "NEU-1", seed=1)
    api = engine.rules_api(0)
    assert api.has_function("controller_has")
    assert api.has_function("win_the_game")
    assert "on_card_played" in RuleEvents.ALL
    # All declared function names must be dynamically resolvable.
    for fn in DECLARED_FUNCTIONS:
        assert hasattr(api, fn)


def test_rules_api_dynamic_fallbacks_basic_contract() -> None:
    cards = [CardDefinition("S", "Santo", "2", 1, 1, "", "NEU-1")]
    engine = GameEngine.create_new(cards, "P1", "P2", "NEU-1", "NEU-1", seed=2)
    api = engine.rules_api(0)
    assert api.count_cards_in_hand(0) == 5
    assert api.target_saint_on_field() == []
    assert api.can_play_only_if(True) is False
    api.win_the_game(0, "test")
    assert engine.state.winner == 0

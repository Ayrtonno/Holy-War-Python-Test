from __future__ import annotations

from typing import Any, cast

from holywar.core.engine import GameEngine
from holywar.data.models import CardDefinition
from holywar.scripting_api import RuleEvents


def test_rules_api_exposes_declared_surface() -> None:
    cards = [CardDefinition("S", "Santo", "2", 1, 1, "", "NEU-1")]
    engine = GameEngine.create_new(cards, "P1", "P2", "NEU-1", "NEU-1", seed=1)
    api = engine.rules_api(0)
    assert api.has_function("controller_has")
    assert api.has_function("win_the_game")
    assert "on_card_played" in RuleEvents.ALL
    assert hasattr(api, "count_cards_in_hand")
    assert hasattr(api, "target_saint_on_field")
    api_any = cast(Any, api)
    assert hasattr(api_any, "can_play_only_if")
    assert api.count_cards_in_hand(0) == 5
    assert api.target_saint_on_field() == []
    assert api_any.can_play_only_if(True) is False
    api.win_the_game(0, "test")
    assert engine.state.winner == 0


def test_rules_api_missing_methods_raise_attribute_error() -> None:
    cards = [CardDefinition("S", "Santo", "2", 1, 1, "", "NEU-1")]
    engine = GameEngine.create_new(cards, "P1", "P2", "NEU-1", "NEU-1", seed=2)
    api = engine.rules_api(0)
    try:
        getattr(api, "definitely_not_real_method")
    except AttributeError:
        pass
    else:
        raise AssertionError("Missing RuleAPI methods must raise AttributeError.")

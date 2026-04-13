from __future__ import annotations

from pathlib import Path

from holywar.core.engine import GameEngine
from holywar.core.state import GameState
from holywar.data.models import CardDefinition


def _cards() -> list[CardDefinition]:
    return [
        CardDefinition("Guerriero", "Santo", "2", 5, 6, "", "Animismo"),
        CardDefinition("Corruzione", "Maledizione", "1", None, None, "", "Neutre"),
    ]


def test_save_and_load_roundtrip(tmp_path: Path) -> None:
    engine = GameEngine.create_new(_cards(), "P1", "P2", "Animismo", "Animismo", seed=5)
    engine.start_turn()
    save_path = tmp_path / "save.json"
    engine.state.save(save_path)

    loaded = GameState.load(save_path)
    assert loaded.turn_number == engine.state.turn_number
    assert loaded.players[0].name == "P1"
    assert len(loaded.instances) == len(engine.state.instances)
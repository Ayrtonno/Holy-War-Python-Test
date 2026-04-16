from __future__ import annotations

import json
from pathlib import Path

from holywar.effects.card_scripts_loader import iter_card_scripts


def test_animismo_and_norrena_decks_are_fully_scripted() -> None:
    rows = json.loads(Path("holywar/data/cards.json").read_text(encoding="utf-8"))
    scripted = {name.strip() for name, _ in iter_card_scripts() if name.strip()}

    for expansion in ("ANI-1", "NOR-1"):
        names = sorted(
            {
                str(row.get("name", "")).strip()
                for row in rows
                if isinstance(row, dict) and row.get("expansion") == expansion and str(row.get("name", "")).strip()
            }
        )
        missing = [name for name in names if name not in scripted]
        assert missing == [], f"{expansion} has missing scripts: {missing}"

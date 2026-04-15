from __future__ import annotations

import json
from pathlib import Path

from holywar.effects.card_scripts_loader import iter_card_scripts


def test_every_card_has_a_dedicated_script_file() -> None:
    cards_path = Path("holywar/data/cards.json")
    rows = json.loads(cards_path.read_text(encoding="utf-8"))
    names = {
        str(r.get("name", "")).strip()
        for r in rows
        if isinstance(r, dict) and str(r.get("name", "")).strip()
    }
    scripted = {name.strip() for name, _ in iter_card_scripts() if name.strip()}
    missing = sorted(names - scripted)
    assert missing == []


def test_card_script_files_are_grouped_under_cards_type_folders() -> None:
    scripts_root = Path("holywar/effects/card_scripts/cards")
    assert scripts_root.exists()
    py_files = [p for p in scripts_root.rglob("*.py") if p.name != "__init__.py"]
    assert py_files
    # Require at least one type folder and enforce shape cards/<type>/<card_file>.py
    assert len({p.parent.name for p in py_files}) >= 2
    for p in py_files:
        rel = p.relative_to(scripts_root).as_posix().split("/")
        assert len(rel) == 2

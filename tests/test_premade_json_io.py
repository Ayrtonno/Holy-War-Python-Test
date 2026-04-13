from __future__ import annotations

import json
from pathlib import Path

from holywar.data.deck_builder import (
    available_premade_decks,
    export_premades_json,
    get_premade_label,
    register_premades_from_json,
    reset_runtime_premades,
)


def test_export_and_import_custom_premade(tmp_path: Path) -> None:
    reset_runtime_premades()
    base_path = tmp_path / "premades_base.json"
    export_premades_json(base_path)
    data = json.loads(base_path.read_text(encoding="utf-8"))
    data["decks"].append(
        {
            "id": "custom_test_deck",
            "religion": "Animismo",
            "name": "Custom Test",
            "cards": [{"name": "Albero Fortunato", "qty": 3}],
        }
    )
    custom_path = tmp_path / "premades_custom.json"
    custom_path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")

    warnings = register_premades_from_json(custom_path)
    assert warnings == []

    ids = {d[0] for d in available_premade_decks("Animismo")}
    assert "custom_test_deck" in ids
    assert "Custom Test" in get_premade_label("custom_test_deck")
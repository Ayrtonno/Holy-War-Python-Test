from __future__ import annotations

from holywar.effects.catalog import (
    BACKLOG_TARGET_IDS,
    CANONICAL_ACTIONS,
    CANONICAL_CONDITIONS,
    CANONICAL_EVENTS,
    CANONICAL_FUNCTIONS,
    current_coverage_snapshot,
    validate_registered_scripts,
)
from holywar.effects.runtime import SUPPORTED_CONDITION_KEYS, SUPPORTED_EFFECT_ACTIONS
from holywar.scripting_api import DECLARED_FUNCTIONS, RuleEvents


def test_backlog_target_count_is_570() -> None:
    assert len(BACKLOG_TARGET_IDS) == 570


def test_canonical_contracts_include_runtime_surfaces() -> None:
    assert set(RuleEvents.ALL).issubset(CANONICAL_EVENTS)
    assert set(DECLARED_FUNCTIONS).issubset(CANONICAL_FUNCTIONS)
    assert set(SUPPORTED_CONDITION_KEYS).issubset(CANONICAL_CONDITIONS)
    assert set(SUPPORTED_EFFECT_ACTIONS).issubset(CANONICAL_ACTIONS)


def test_coverage_snapshot_shape() -> None:
    snap = current_coverage_snapshot()
    assert snap.target_total == 570
    assert snap.implemented_events >= len(RuleEvents.ALL)
    assert snap.implemented_functions >= len(DECLARED_FUNCTIONS)
    assert snap.implemented_conditions >= len(SUPPORTED_CONDITION_KEYS)
    assert snap.implemented_actions >= len(SUPPORTED_EFFECT_ACTIONS)
    assert snap.script_count > 0
    assert snap.target_ratio > 0


def test_registered_runtime_scripts_use_known_catalog_entries() -> None:
    result = validate_registered_scripts()
    assert result["unknown_events"] == []
    assert result["unknown_actions"] == []
    assert result["unknown_condition_keys"] == []


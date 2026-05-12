from __future__ import annotations

import json
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Any

from holywar.effects.card_scripts_loader import iter_card_scripts
import unicodedata


def _norm(text: str) -> str:
    value = unicodedata.normalize("NFKD", text or "")
    value = "".join(ch for ch in value if not unicodedata.combining(ch))
    return value.strip().lower()


SUMMON_ACTIONS = {
    "summon_target_to_field",
    "summon_target_to_field_pay_half_inspiration",
    "summon_card_from_hand",
    "summon_named_card",
    "summon_named_card_from_flag",
    "summon_generated_token",
    "summon_generated_token_in_each_free_saint_slot",
    "summon_stored_card_to_field",
    "choose_targets_and_summon_to_field",
}


@dataclass(slots=True)
class Finding:
    card: str
    section: str
    index: int
    severity: str
    code: str
    message: str


def _has_key(d: dict[str, Any], key: str) -> bool:
    return key in d and d.get(key) is not None


def _iter_action_sections(spec: dict[str, Any]) -> list[tuple[str, list[dict[str, Any]]]]:
    out: list[tuple[str, list[dict[str, Any]]]] = []
    for name in ("on_play_actions", "on_enter_actions", "on_activate_actions"):
        raw = spec.get(name, [])
        if isinstance(raw, list):
            out.append((name, [x for x in raw if isinstance(x, dict)]))
    return out


def audit_card(card_name: str, spec: dict[str, Any]) -> list[Finding]:
    findings: list[Finding] = []
    has_default_target_policy = _has_key(spec, "default_target_policy")
    has_default_selection_mode = _has_key(spec, "default_selection_mode")
    has_default_cancel_behavior = _has_key(spec, "default_cancel_behavior")
    has_default_placement_policy = _has_key(spec, "default_placement_policy")
    has_default_activation_mode = _has_key(spec, "default_activation_mode")

    if not has_default_target_policy:
        findings.append(
            Finding(
                card=card_name,
                section="card",
                index=-1,
                severity="warning",
                code="missing.default_target_policy",
                message="Manca default_target_policy a livello carta.",
            )
        )
    if not has_default_selection_mode:
        findings.append(
            Finding(
                card=card_name,
                section="card",
                index=-1,
                severity="warning",
                code="missing.default_selection_mode",
                message="Manca default_selection_mode a livello carta.",
            )
        )
    if not has_default_cancel_behavior:
        findings.append(
            Finding(
                card=card_name,
                section="card",
                index=-1,
                severity="warning",
                code="missing.default_cancel_behavior",
                message="Manca default_cancel_behavior a livello carta.",
            )
        )
    if not has_default_placement_policy:
        findings.append(
            Finding(
                card=card_name,
                section="card",
                index=-1,
                severity="warning",
                code="missing.default_placement_policy",
                message="Manca default_placement_policy a livello carta.",
            )
        )
    if not has_default_activation_mode:
        findings.append(
            Finding(
                card=card_name,
                section="card",
                index=-1,
                severity="warning",
                code="missing.default_activation_mode",
                message="Manca default_activation_mode a livello carta.",
            )
        )

    for section, actions in _iter_action_sections(spec):
        for idx, action in enumerate(actions):
            target = action.get("target")
            effect = action.get("effect")

            if isinstance(target, dict):
                if not _has_key(target, "target_policy"):
                    findings.append(
                        Finding(
                            card=card_name,
                            section=section,
                            index=idx,
                            severity="warning" if has_default_target_policy else "error",
                            code="missing.target_policy",
                            message="TargetSpec senza target_policy esplicita.",
                        )
                    )
                if not _has_key(target, "selection_mode"):
                    findings.append(
                        Finding(
                            card=card_name,
                            section=section,
                            index=idx,
                            severity="warning" if has_default_selection_mode else "error",
                            code="missing.selection_mode",
                            message="TargetSpec senza selection_mode esplicita.",
                        )
                    )
                if not _has_key(target, "cancel_behavior"):
                    findings.append(
                        Finding(
                            card=card_name,
                            section=section,
                            index=idx,
                            severity="warning" if has_default_cancel_behavior else "error",
                            code="missing.cancel_behavior",
                            message="TargetSpec senza cancel_behavior esplicito.",
                        )
                    )

            if not _has_key(action, "activation_mode"):
                findings.append(
                    Finding(
                        card=card_name,
                        section=section,
                        index=idx,
                        severity="warning" if has_default_activation_mode else "error",
                        code="missing.activation_mode",
                        message="ActionSpec senza activation_mode esplicita.",
                    )
                )

            if isinstance(effect, dict):
                effect_action = _norm(str(effect.get("action", "")))
                if effect_action in SUMMON_ACTIONS and not _has_key(effect, "placement_policy"):
                    findings.append(
                        Finding(
                            card=card_name,
                            section=section,
                            index=idx,
                            severity="warning" if has_default_placement_policy else "error",
                            code="missing.placement_policy",
                            message="Azione summon senza placement_policy esplicita.",
                        )
                    )
    return findings


def main() -> None:
    findings: list[Finding] = []
    cards = list(iter_card_scripts())
    for card_name, spec in cards:
        findings.extend(audit_card(card_name, spec or {}))

    out_dir = Path("docs") / "reports"
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / "script_policy_audit.json"
    out_path.write_text(json.dumps([asdict(f) for f in findings], ensure_ascii=False, indent=2), encoding="utf-8")

    total = len(cards)
    errors = sum(1 for f in findings if f.severity == "error")
    warnings = sum(1 for f in findings if f.severity == "warning")
    print(f"Cards scanned: {total}")
    print(f"Findings: {len(findings)} (errors={errors}, warnings={warnings})")
    print(f"Report: {out_path}")


if __name__ == "__main__":
    main()

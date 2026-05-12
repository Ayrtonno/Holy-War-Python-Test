from __future__ import annotations

from pathlib import Path
import re


CARD_SCRIPTS_ROOT = Path("holywar/effects/card_scripts/cards")
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


def _count_delta(line: str) -> int:
    return line.count("{") - line.count("}")


def _indent_of(line: str) -> str:
    return line[: len(line) - len(line.lstrip(" "))]


def _policy_from_target_block(block: str) -> str:
    matches = re.findall(r'"min_targets"\s*:\s*(\d+)', block)
    if not matches:
        return "optional_resolve"
    max_min = max(int(v) for v in matches)
    if max_min > 0:
        return "required_to_resolve"
    return "optional_resolve"


def patch_file(path: Path) -> bool:
    src = path.read_text(encoding="utf-8")

    lines = src.splitlines()
    out: list[str] = []
    changed = False

    i = 0
    while i < len(lines):
        line = lines[i]
        stripped = line.strip()

        # target policy normalization
        if '"target": {' in stripped:
            block_lines = [line]
            depth = _count_delta(line)
            i += 1
            while i < len(lines):
                block_lines.append(lines[i])
                depth += _count_delta(lines[i])
                if depth <= 0:
                    break
                i += 1

            block_text = "\n".join(block_lines)
            has_target_policy = '"target_policy"' in block_text
            has_selection_mode = '"selection_mode"' in block_text
            has_cancel_behavior = '"cancel_behavior"' in block_text

            if not (has_target_policy and has_selection_mode and has_cancel_behavior):
                closing_idx = len(block_lines) - 1
                base_indent = _indent_of(block_lines[0]) + "    "
                inserts: list[str] = []
                if not has_target_policy:
                    inserts.append(f'{base_indent}"target_policy": "{_policy_from_target_block(block_text)}",')
                if not has_selection_mode:
                    inserts.append(f'{base_indent}"selection_mode": "prompt",')
                if not has_cancel_behavior:
                    inserts.append(f'{base_indent}"cancel_behavior": "abort_step",')
                if inserts:
                    block_lines = block_lines[:closing_idx] + inserts + block_lines[closing_idx:]
                    changed = True

            out.extend(block_lines)
            i += 1
            continue

        # summon placement policy normalization
        if '"effect": {' in stripped:
            block_lines = [line]
            depth = _count_delta(line)
            i += 1
            while i < len(lines):
                block_lines.append(lines[i])
                depth += _count_delta(lines[i])
                if depth <= 0:
                    break
                i += 1

            block_text = "\n".join(block_lines)
            is_summon = any(f'"action": "{a}"' in block_text for a in SUMMON_ACTIONS)
            has_placement = '"placement_policy"' in block_text
            if is_summon and not has_placement:
                closing_idx = len(block_lines) - 1
                base_indent = _indent_of(block_lines[0]) + "    "
                block_lines = (
                    block_lines[:closing_idx]
                    + [f'{base_indent}"placement_policy": "prompt_slot_required",']
                    + block_lines[closing_idx:]
                )
                changed = True

            out.extend(block_lines)
            i += 1
            continue

        out.append(line)
        i += 1

    if changed:
        path.write_text("\n".join(out) + ("\n" if src.endswith("\n") else ""), encoding="utf-8")
    return changed


def main() -> None:
    files = sorted(CARD_SCRIPTS_ROOT.rglob("*.py"))
    changed = 0
    for file in files:
        if patch_file(file):
            changed += 1
    print(f"Scanned: {len(files)}")
    print(f"Updated files: {changed}")


if __name__ == "__main__":
    main()

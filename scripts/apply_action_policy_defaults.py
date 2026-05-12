from __future__ import annotations

from pathlib import Path


CARD_SCRIPTS_ROOT = Path("holywar/effects/card_scripts/cards")

ACTION_LIST_KEYS = ('"on_play_actions"', '"on_enter_actions"', '"on_activate_actions"')
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


def _line_indent(line: str) -> str:
    return line[: len(line) - len(line.lstrip(" "))]


def _count_delta(line: str) -> int:
    return line.count("{") - line.count("}")


def patch_file(path: Path) -> bool:
    src = path.read_text(encoding="utf-8")
    lines = src.splitlines()
    out: list[str] = []
    changed = False

    in_actions = False
    list_depth = 0
    in_entry = False
    entry_depth = 0
    entry_lines: list[str] = []

    def flush_entry() -> None:
        nonlocal changed, entry_lines
        if not entry_lines:
            return
        text = "\n".join(entry_lines)
        has_activation_mode = '"activation_mode"' in text
        has_effect = '"effect"' in text

        new_lines = list(entry_lines)

        if not has_activation_mode:
            # inject after first opening line of entry
            for i, ln in enumerate(new_lines):
                if "{" in ln:
                    indent = _line_indent(ln) + "    "
                    new_lines.insert(i + 1, f'{indent}"activation_mode": "mandatory_auto",')
                    changed = True
                    break

        # summon placement policy inside effect block
        entry_text = "\n".join(new_lines)
        is_summon = any(f'"action": "{a}"' in entry_text for a in SUMMON_ACTIONS)
        has_placement = '"placement_policy"' in entry_text
        if is_summon and has_effect and not has_placement:
            for i, ln in enumerate(new_lines):
                if '"action": "' in ln and any(f'"action": "{a}"' in ln for a in SUMMON_ACTIONS):
                    indent = _line_indent(ln)
                    new_lines.insert(i + 1, f'{indent}"placement_policy": "prompt_slot_required",')
                    changed = True
                    break

        out.extend(new_lines)
        entry_lines = []

    for line in lines:
        stripped = line.strip()
        if not in_actions and any(k in stripped for k in ACTION_LIST_KEYS) and stripped.endswith("["):
            in_actions = True
            list_depth = 1
            out.append(line)
            continue

        if in_actions:
            # top-level list close
            if not in_entry and stripped == "],":
                in_actions = False
                list_depth = 0
                out.append(line)
                continue

            if not in_entry:
                if stripped.startswith("{"):
                    in_entry = True
                    entry_depth = _count_delta(line)
                    entry_lines = [line]
                    if entry_depth <= 0:
                        flush_entry()
                        in_entry = False
                        entry_depth = 0
                else:
                    out.append(line)
                continue

            # in_entry
            entry_lines.append(line)
            entry_depth += _count_delta(line)
            if entry_depth <= 0:
                flush_entry()
                in_entry = False
                entry_depth = 0
            continue

        out.append(line)

    if in_entry:
        flush_entry()

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
    print(f"Updated: {changed}")


if __name__ == "__main__":
    main()

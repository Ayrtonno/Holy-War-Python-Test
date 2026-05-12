from __future__ import annotations

from pathlib import Path


CARD_SCRIPTS_ROOT = Path("holywar/effects/card_scripts/cards")
ACTION_LIST_KEYS = ('"on_play_actions"', '"on_enter_actions"', '"on_activate_actions"')


def _count_delta(line: str) -> int:
    return line.count("{") - line.count("}")


def sanitize_file(path: Path) -> bool:
    src = path.read_text(encoding="utf-8")
    lines = src.splitlines()
    out: list[str] = []
    changed = False

    in_actions = False
    in_entry = False
    entry_depth = 0

    for line in lines:
        stripped = line.strip()

        if not in_actions and any(k in stripped for k in ACTION_LIST_KEYS) and stripped.endswith("["):
            in_actions = True
            out.append(line)
            continue

        if in_actions:
            if not in_entry and stripped == "],":
                in_actions = False
                out.append(line)
                continue

            if not in_entry:
                # Invalid leftovers inserted outside dict entry: drop them.
                if stripped == '"activation_mode": "mandatory_auto",':
                    changed = True
                    continue
                if stripped == '"placement_policy": "prompt_slot_required",':
                    changed = True
                    continue
                if stripped.startswith("{"):
                    in_entry = True
                    entry_depth = _count_delta(line)
                    out.append(line)
                    if entry_depth <= 0:
                        in_entry = False
                        entry_depth = 0
                    continue
                out.append(line)
                continue

            out.append(line)
            entry_depth += _count_delta(line)
            if entry_depth <= 0:
                in_entry = False
                entry_depth = 0
            continue

        out.append(line)

    if changed:
        path.write_text("\n".join(out) + ("\n" if src.endswith("\n") else ""), encoding="utf-8")
    return changed


def main() -> None:
    files = sorted(CARD_SCRIPTS_ROOT.rglob("*.py"))
    changed = 0
    for file in files:
        if sanitize_file(file):
            changed += 1
    print(f"Scanned: {len(files)}")
    print(f"Sanitized: {changed}")


if __name__ == "__main__":
    main()


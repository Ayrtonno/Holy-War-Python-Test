from __future__ import annotations

from pathlib import Path


CARD_SCRIPTS_ROOT = Path("holywar/effects/card_scripts/cards")

DEFAULT_LINES = [
    '    "default_target_policy": "optional_resolve",',
    '    "default_selection_mode": "prompt",',
    '    "default_cancel_behavior": "abort_step",',
    '    "default_placement_policy": "prompt_slot_required",',
    '    "default_activation_mode": "mandatory_auto",',
]


def patch_file(path: Path) -> bool:
    text = path.read_text(encoding="utf-8")
    if "SCRIPT = {" not in text:
        return False

    lines = text.splitlines()
    out: list[str] = []
    changed = False
    inserted = False

    for line in lines:
        out.append(line)
        if not inserted and line.strip() == "SCRIPT = {":
            for dline in DEFAULT_LINES:
                if dline not in text:
                    out.append(dline)
                    changed = True
            inserted = True

    if changed:
        path.write_text("\n".join(out) + ("\n" if text.endswith("\n") else ""), encoding="utf-8")
    return changed


def main() -> None:
    files = sorted(CARD_SCRIPTS_ROOT.rglob("*.py"))
    changed = 0
    for path in files:
        if patch_file(path):
            changed += 1
    print(f"Scanned: {len(files)}")
    print(f"Updated: {changed}")


if __name__ == "__main__":
    main()

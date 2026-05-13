from __future__ import annotations

import json
import re
import unicodedata
from pathlib import Path

ROOT = Path("holywar/effects/card_scripts/cards")
REPORT = Path("docs/reports/script_policy_audit.json")


def _norm(v: str) -> str:
    s = unicodedata.normalize("NFKD", v or "")
    s = "".join(ch for ch in s if not unicodedata.combining(ch))
    return s.strip().lower()


def _module_path_for_card(card_name: str) -> Path | None:
    wanted = _norm(card_name)
    for p in ROOT.rglob("*.py"):
        txt = p.read_text(encoding="utf-8")
        m = re.search(r'CARD_NAME\s*=\s*["\'](.+?)["\']', txt)
        if m and _norm(m.group(1)) == wanted:
            return p
    return None


def _count_delta(s: str) -> int:
    return s.count("{") - s.count("}")


TARGET_START_RE = re.compile(r"""["']target["']\s*:\s*\{""")
EFFECT_START_RE = re.compile(r"""["']effect["']\s*:\s*\{""")
POLICY_LINE_RE = re.compile(r"""^\s*["'](target_policy|selection_mode|cancel_behavior)["']\s*:\s*["']([^"']+)["']\s*,?\s*$""")
ACTION_LINE_RE = re.compile(r"""["']action["']\s*:\s*["']([^"']+)["']""")
ACTIVATION_LINE_RE = re.compile(r"""^\s*["']activation_mode["']\s*:\s*["']mandatory_auto["']\s*,?\s*$""")
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


def _quote_for_block(block: list[str]) -> str:
    txt = "\n".join(block)
    if "'" in txt and '"' not in txt:
        return "'"
    return '"'


def _target_policy_guess(txt: str) -> str:
    mins = re.findall(r"""["']min_targets["']\s*:\s*(\d+)""", txt)
    if mins and max(int(v) for v in mins) > 0:
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

        # normalize target blocks
        if TARGET_START_RE.search(stripped):
            block = [line]
            depth = _count_delta(line)
            i += 1
            while i < len(lines) and depth > 0:
                block.append(lines[i])
                depth += _count_delta(lines[i])
                i += 1
            q = _quote_for_block(block)
            block_txt = "\n".join(block)
            has_tp = ("target_policy" in block_txt)
            has_sm = ("selection_mode" in block_txt)
            has_cb = ("cancel_behavior" in block_txt)

            collected: dict[str, str] = {}
            # swallow misplaced immediate policy lines after target block
            while i < len(lines):
                m = POLICY_LINE_RE.match(lines[i])
                if not m:
                    break
                collected[m.group(1)] = m.group(2)
                i += 1
                changed = True

            inserts: list[str] = []
            indent = re.match(r"^(\s*)", block[0]).group(1) + "    "
            if not has_tp:
                tp = collected.get("target_policy", _target_policy_guess(block_txt))
                inserts.append(f"{indent}{q}target_policy{q}: {q}{tp}{q},")
            if not has_sm:
                sm = collected.get("selection_mode", "prompt")
                inserts.append(f"{indent}{q}selection_mode{q}: {q}{sm}{q},")
            if not has_cb:
                cb = collected.get("cancel_behavior", "abort_step")
                inserts.append(f"{indent}{q}cancel_behavior{q}: {q}{cb}{q},")
            if inserts:
                close_idx = len(block) - 1
                block = block[:close_idx] + inserts + block[close_idx:]
                changed = True
            out.extend(block)
            continue

        # normalize effect summon placement policy
        if EFFECT_START_RE.search(stripped):
            block = [line]
            depth = _count_delta(line)
            i += 1
            while i < len(lines) and depth > 0:
                block.append(lines[i])
                depth += _count_delta(lines[i])
                i += 1
            txt = "\n".join(block)
            if "placement_policy" not in txt:
                action_match = ACTION_LINE_RE.search(txt)
                if action_match and action_match.group(1) in SUMMON_ACTIONS:
                    q = _quote_for_block(block)
                    indent = re.match(r"^(\s*)", block[0]).group(1) + "    "
                    close_idx = len(block) - 1
                    block = block[:close_idx] + [f"{indent}{q}placement_policy{q}: {q}prompt_slot_required{q},"] + block[close_idx:]
                    changed = True
            out.extend(block)
            continue

        # remove stray activation_mode outside blocks (rare leftovers)
        if ACTIVATION_LINE_RE.match(stripped):
            changed = True
            i += 1
            continue

        out.append(line)
        i += 1
    if changed:
        path.write_text("\n".join(out) + ("\n" if src.endswith("\n") else ""), encoding="utf-8")
    return changed


def main() -> None:
    report = json.loads(REPORT.read_text(encoding="utf-8"))
    cards = sorted(
        {
            item["card"]
            for item in report
            if item.get("severity") == "warning"
            and item.get("code")
            in {
                "missing.target_policy",
                "missing.selection_mode",
                "missing.cancel_behavior",
                "missing.placement_policy",
                "missing.activation_mode",
            }
        }
    )
    changed = 0
    for card in cards:
        p = _module_path_for_card(card)
        if p and patch_file(p):
            changed += 1
    print(f"cards={len(cards)} changed={changed}")


if __name__ == "__main__":
    main()


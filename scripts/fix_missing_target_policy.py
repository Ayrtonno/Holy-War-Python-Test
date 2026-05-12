from __future__ import annotations

import json
from pathlib import Path
import re
import unicodedata

ROOT = Path("holywar/effects/card_scripts/cards")
REPORT = Path("docs/reports/script_policy_audit.json")


def _module_path_for_card(card_name: str) -> Path | None:
    def norm(v: str) -> str:
        s = unicodedata.normalize("NFKD", v or "")
        s = "".join(ch for ch in s if not unicodedata.combining(ch))
        return s.strip().lower()
    key = norm(card_name)
    for p in ROOT.rglob("*.py"):
        txt = p.read_text(encoding="utf-8")
        m = re.search(r'CARD_NAME\s*=\s*["\'](.+?)["\']', txt)
        if m and norm(m.group(1)) == key:
            return p
    return None


def _count_delta(s: str) -> int:
    return s.count("{") - s.count("}")


def _policy_for_target_block(txt: str) -> str:
    m = re.findall(r'"min_targets"\s*:\s*(\d+)', txt)
    if m and max(int(x) for x in m) > 0:
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
        if not re.search(r"""["']target["']\s*:\s*\{""", stripped):
            out.append(line)
            i += 1
            continue

        block = [line]
        depth = _count_delta(line)
        i += 1
        while i < len(lines) and depth > 0:
            block.append(lines[i])
            depth += _count_delta(lines[i])
            i += 1
        txt = "\n".join(block)
        has_tp = '"target_policy"' in txt or "'target_policy'" in txt
        has_sm = '"selection_mode"' in txt or "'selection_mode'" in txt
        has_cb = '"cancel_behavior"' in txt or "'cancel_behavior'" in txt
        if has_tp and has_sm and has_cb:
            out.extend(block)
            continue

        policy = _policy_for_target_block(txt)
        if len(block) == 1 and "}" in block[0]:
            ln = block[0]
            idx = ln.find("{") + 1
            quote = "'" if "'target': {" in ln or ("'" in ln and '"' not in ln) else '"'
            inserts = []
            if not has_tp:
                inserts.append(f" {quote}target_policy{quote}: {quote}{policy}{quote},")
            if not has_sm:
                inserts.append(f" {quote}selection_mode{quote}: {quote}prompt{quote},")
            if not has_cb:
                inserts.append(f" {quote}cancel_behavior{quote}: {quote}abort_step{quote},")
            ln2 = ln[:idx] + "".join(inserts) + ln[idx:]
            out.append(ln2)
            changed = True
            continue

        indent = re.match(r"^(\s*)", block[0]).group(1) + "    "
        use_single = any("'" in bl and '"' not in bl for bl in block)
        ins: list[str] = []
        if not has_tp:
            if use_single:
                ins.append(f"{indent}'target_policy': '{policy}',")
            else:
                ins.append(f'{indent}"target_policy": "{policy}",')
        if not has_sm:
            if use_single:
                ins.append(f"{indent}'selection_mode': 'prompt',")
            else:
                ins.append(f'{indent}"selection_mode": "prompt",')
        if not has_cb:
            if use_single:
                ins.append(f"{indent}'cancel_behavior': 'abort_step',")
            else:
                ins.append(f'{indent}"cancel_behavior": "abort_step",')
        close_idx = len(block) - 1
        block = block[:close_idx] + ins + block[close_idx:]
        out.extend(block)
        changed = True
    if changed:
        path.write_text("\n".join(out) + ("\n" if src.endswith("\n") else ""), encoding="utf-8")
    return changed


def main() -> None:
    report = json.loads(REPORT.read_text(encoding="utf-8"))
    cards = sorted({item["card"] for item in report if item.get("code") == "missing.target_policy"})
    changed = 0
    for card in cards:
        p = _module_path_for_card(card)
        if p and patch_file(p):
            changed += 1
    print(f"cards={len(cards)} changed={changed}")


if __name__ == "__main__":
    main()

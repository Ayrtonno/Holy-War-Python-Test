from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable
import json
import unicodedata

from holywar.app_paths import appdata_dir, bundled_data_dir
from holywar.data.models import CardDefinition
from holywar.data.premade_decks import NEUTRAL_FILL_ORDER


CANONICAL_RELIGIONS = [
    "Cristianesimo",
    "Mitologia Norrena",
    "Animismo",
    "Egiziane",
    "Ph-DakGaph",
    "Ombre Maya",
]

RELIGION_ALIASES = {
    "Cristianesimo": {"Cristianesimo", "CRI-1"},
    "Mitologia Norrena": {"Mitologia Norrena", "NOR-1"},
    "Animismo": {"Animismo", "ANI-1"},
    "Egiziane": {"Egiziane", "EGI-1"},
    "Ph-DakGaph": {"Ph-DakGaph", "PHD-1"},
    "Ombre Maya": {"Ombre Maya", "MAY-1"},
    "Neutre": {"Neutre", "NEU-1"},
}

TYPE_PRIORITY = {
    "santo": 0,
    "artefatto": 1,
    "edificio": 2,
    "benedizione": 3,
    "maledizione": 4,
    "innata": 5,
    "token": 6,
}


@dataclass(slots=True)
class DeckBuildResult:
    main_deck: list[CardDefinition]
    white_deck: list[CardDefinition]
    innate_deck: list[CardDefinition]


@dataclass(slots=True)
class PremadeBuild:
    deck: DeckBuildResult
    warnings: list[str]


_FALLBACK_PREMADE_STORE_PATH = Path("holywar/data/premade_decks.json")
_DEFAULT_PREMADE_SOURCE_PATH = bundled_data_dir() / "premade_decks.json"
_LEGACY_PREMADE_PATHS = [
    Path("holywar/data/premade_decks.json"),
    Path("holywar/data/user_decks.json"),
]
_RUNTIME_PREMADE_DECKS: dict[str, dict] = {}


def _resolve_premade_store_path() -> Path:
    primary = appdata_dir() / "premade_decks.json"
    for candidate in (primary, _FALLBACK_PREMADE_STORE_PATH):
        try:
            candidate.parent.mkdir(parents=True, exist_ok=True)
            return candidate
        except Exception:
            continue
    return _FALLBACK_PREMADE_STORE_PATH


PREMADE_STORE_PATH = _resolve_premade_store_path()


def _is_in_group(card: CardDefinition, canonical: str) -> bool:
    aliases = RELIGION_ALIASES.get(canonical, {canonical})
    return card.expansion in aliases


def _cross_value(crosses: str) -> int | None:
    text = (crosses or "").strip().lower()
    if text in {"white", "croce bianca"}:
        return 11
    try:
        return int(float(text))
    except ValueError:
        return None


def _copy_limits(card: CardDefinition) -> tuple[int, str]:
    value = _cross_value(card.crosses)
    if value is None:
        return 1, "unknown"
    if 1 <= value <= 3:
        return 5, "low"
    if 4 <= value <= 6:
        return 3, "mid"
    if 7 <= value <= 9:
        return 1, "high"
    if value == 10:
        return 1, "ten"
    if value >= 11:
        return 1, "white"
    return 1, "unknown"


def _sort_cards(cards: Iterable[CardDefinition]) -> list[CardDefinition]:
    return sorted(
        cards,
        key=lambda c: (
            TYPE_PRIORITY.get(c.card_type.lower(), 99),
            (c.faith if c.faith is not None else 0),
            c.name,
        ),
    )


def _norm(text: str) -> str:
    value = (
        text.replace("’", "'")
        .replace("`", "'")
        .replace("ø", "o")
        .replace("Ø", "O")
        .replace("ð", "d")
        .replace("Ð", "D")
    )
    value = unicodedata.normalize("NFKD", value)
    value = "".join(ch for ch in value if not unicodedata.combining(ch))
    return value.strip().lower()


def available_religions(cards: list[CardDefinition]) -> list[str]:
    present_from_cards = {rel for rel in CANONICAL_RELIGIONS if any(_is_in_group(c, rel) for c in cards)}
    present_from_premades = {str(cfg.get("religion", "")).strip() for cfg in _RUNTIME_PREMADE_DECKS.values()}
    out: list[str] = []
    for rel in CANONICAL_RELIGIONS:
        if rel in present_from_cards or rel in present_from_premades:
            out.append(rel)
    return out


def available_premade_decks(religion: str | None = None) -> list[tuple[str, str, str]]:
    out: list[tuple[str, str, str]] = []
    for deck_id, cfg in _RUNTIME_PREMADE_DECKS.items():
        rel = cfg["religion"]
        if religion and rel != religion:
            continue
        out.append((deck_id, rel, cfg["name"]))
    out.sort(key=lambda x: (x[1], x[2]))
    return out


def get_runtime_premade(deck_id: str) -> dict | None:
    cfg = _RUNTIME_PREMADE_DECKS.get(str(deck_id))
    if cfg is None:
        return None
    return {
        "id": str(deck_id),
        "religion": str(cfg.get("religion", "")),
        "name": str(cfg.get("name", "")),
        "cards": list(cfg.get("cards", []) or []),
        "allow_over_45": bool(cfg.get("allow_over_45", False)),
    }


def runtime_premade_decks() -> list[dict]:
    out: list[dict] = []
    for deck_id, cfg in _RUNTIME_PREMADE_DECKS.items():
        out.append(
            {
                "id": str(deck_id),
                "religion": str(cfg.get("religion", "")),
                "name": str(cfg.get("name", "")),
                "cards": list(cfg.get("cards", []) or []),
                "allow_over_45": bool(cfg.get("allow_over_45", False)),
            }
        )
    out.sort(key=lambda d: (str(d.get("religion", "")), str(d.get("name", ""))))
    return out


def get_premade_label(deck_id: str) -> str:
    cfg = _RUNTIME_PREMADE_DECKS[deck_id]
    return f"{cfg['religion']} - {cfg['name']}"


def reset_runtime_premades() -> None:
    _RUNTIME_PREMADE_DECKS.clear()
    _ensure_premade_store_exists()
    if PREMADE_STORE_PATH.exists():
        register_premades_from_json(PREMADE_STORE_PATH)


def _ensure_premade_store_exists() -> None:
    if PREMADE_STORE_PATH.exists():
        return
    PREMADE_STORE_PATH.parent.mkdir(parents=True, exist_ok=True)

    for legacy in _LEGACY_PREMADE_PATHS:
        try:
            if not legacy.exists():
                continue
            src = legacy.resolve()
            dst = PREMADE_STORE_PATH.resolve()
            if src == dst:
                return
            PREMADE_STORE_PATH.write_text(legacy.read_text(encoding="utf-8"), encoding="utf-8")
            return
        except Exception:
            continue

    if _DEFAULT_PREMADE_SOURCE_PATH.exists():
        PREMADE_STORE_PATH.write_text(_DEFAULT_PREMADE_SOURCE_PATH.read_text(encoding="utf-8"), encoding="utf-8")
        return

    PREMADE_STORE_PATH.write_text(json.dumps({"decks": []}, ensure_ascii=False, indent=2), encoding="utf-8")


def _normalize_deck_payload(item: dict) -> dict:
    deck_id = str(item["id"]).strip()
    religion = str(item["religion"]).strip()
    name = str(item["name"]).strip()
    cards_payload = item.get("cards", [])
    cards: list[tuple[str, int]] = []
    for c in cards_payload:
        if isinstance(c, dict):
            cname = str(c.get("name", "")).strip()
            qty = int(c.get("qty", 1))
        else:
            continue
        if cname and qty > 0:
            cards.append((cname, qty))
    return {
        "id": deck_id,
        "religion": religion,
        "name": name,
        "cards": cards,
        "allow_over_45": bool(item.get("allow_over_45", False)),
    }


def register_premades_from_json(path: str | Path) -> list[str]:
    data = json.loads(Path(path).read_text(encoding="utf-8"))
    decks = data.get("decks", [])
    warnings: list[str] = []
    if not isinstance(decks, list):
        warnings.append("Formato JSON non valido: 'decks' deve essere una lista.")
        return warnings
    for raw in decks:
        if not isinstance(raw, dict):
            warnings.append("Entry deck non valida (non dict), ignorata.")
            continue
        try:
            deck = _normalize_deck_payload(raw)
            if not deck["id"] or not deck["religion"] or not deck["name"]:
                warnings.append("Deck con id/religion/name vuoti, ignorato.")
                continue
            _RUNTIME_PREMADE_DECKS[deck["id"]] = {
                "religion": deck["religion"],
                "name": deck["name"],
                "cards": deck["cards"],
                "allow_over_45": bool(deck.get("allow_over_45", False)),
            }
        except Exception as exc:
            warnings.append(f"Deck non valido: {exc}")
    return warnings


def export_premades_json(path: str | Path, include_builtin: bool = True) -> Path:
    _ = include_builtin
    src = _RUNTIME_PREMADE_DECKS
    payload = {
        "decks": [
            {
                "id": deck_id,
                "religion": cfg["religion"],
                "name": cfg["name"],
                "allow_over_45": bool(cfg.get("allow_over_45", False)),
                "cards": [{"name": n, "qty": q} for n, q in cfg["cards"]],
            }
            for deck_id, cfg in src.items()
        ]
    }
    out = Path(path)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    return out


def disable_runtime_premade(deck_id: str) -> None:
    _ = deck_id
    return


def build_test_deck(cards: list[CardDefinition], religion: str) -> DeckBuildResult:
    religion_cards = [
        c for c in cards
        if _is_in_group(c, religion)
    ]
    neutral_cards = [
        c for c in cards
        if _is_in_group(c, "Neutre")
    ]

    if not religion_cards:
        religion_cards = [c for c in cards if c.expansion == religion]

    base_pool = [
        c for c in religion_cards + neutral_cards
        if c.card_type.lower() not in {"token", "innata"}
    ]
    white_pool = [c for c in religion_cards if c.card_type.lower() == "token"]
    innate_pool = [
        c for c in religion_cards + neutral_cards
        if c.card_type.lower() == "innata"
    ]

    base_pool = _sort_cards(base_pool)
    by_name: dict[str, CardDefinition] = {}
    for card in base_pool:
        by_name.setdefault(card.name, card)

    chosen: list[CardDefinition] = []
    per_card = defaultdict(int)
    band_count = defaultdict(int)

    # First pass: one copy per card if legal, in deterministic order.
    for card in by_name.values():
        max_copy, band = _copy_limits(card)
        if max_copy <= 0:
            continue
        if band == "high" and band_count[band] >= 10:
            continue
        if band == "ten" and band_count[band] >= 3:
            continue
        if band == "white" and band_count[band] >= 1:
            continue
        chosen.append(card)
        per_card[card.name] += 1
        band_count[band] += 1
        if len(chosen) >= 45:
            break

    # Second pass: add extra copies until 45.
    if len(chosen) < 45:
        fill_order = _sort_cards(by_name.values())
        changed = True
        while len(chosen) < 45 and changed:
            changed = False
            for card in fill_order:
                max_copy, band = _copy_limits(card)
                if per_card[card.name] >= max_copy:
                    continue
                if band == "high" and band_count[band] >= 10:
                    continue
                if band == "ten" and band_count[band] >= 3:
                    continue
                if band == "white" and band_count[band] >= 1:
                    continue
                chosen.append(card)
                per_card[card.name] += 1
                band_count[band] += 1
                changed = True
                if len(chosen) >= 45:
                    break

    # Last resort for tiny test pools: allow duplicates up to 45.
    if len(chosen) < 45 and by_name:
        fallback = list(by_name.values())
        idx = 0
        while len(chosen) < 45:
            chosen.append(fallback[idx % len(fallback)])
            idx += 1

    white_deck: list[CardDefinition] = []
    for token in _sort_cards(white_pool):
        for _ in range(5):
            white_deck.append(token)

    return DeckBuildResult(main_deck=chosen[:45], white_deck=white_deck, innate_deck=_sort_cards(innate_pool))


def build_premade_deck(cards: list[CardDefinition], deck_id: str) -> PremadeBuild:
    cfg = _RUNTIME_PREMADE_DECKS[deck_id]
    religion = cfg["religion"]
    allow_over_45 = bool(cfg.get("allow_over_45", False))
    warnings: list[str] = []

    by_name: dict[str, CardDefinition] = {}
    for c in cards:
        by_name.setdefault(_norm(c.name), c)

    main: list[CardDefinition] = []
    white: list[CardDefinition] = []
    innate: list[CardDefinition] = []

    def add_card(name: str, qty: int, source: str) -> None:
        card = by_name.get(_norm(name))
        if card is None:
            warnings.append(f"{source}: carta non trovata -> {name}")
            return
        ctype = card.card_type.lower()
        if ctype == "token":
            target = white
        elif ctype == "innata":
            target = innate
        else:
            target = main
        for _ in range(max(0, qty)):
            target.append(card)

    for name, qty in cfg["cards"]:
        add_card(name, qty, cfg["name"])

    # Fill with suggested neutral package if under 45.
    if len(main) < 45:
        for name, qty in NEUTRAL_FILL_ORDER:
            if len(main) >= 45:
                break
            card = by_name.get(_norm(name))
            if card is None or card.card_type.lower() in {"token", "innata"}:
                continue
            for _ in range(qty):
                if len(main) >= 45:
                    break
                main.append(card)

    # Fallback with auto test deck of same religion.
    if len(main) < 45:
        auto = build_test_deck(cards, religion).main_deck
        idx = 0
        while len(main) < 45 and auto:
            main.append(auto[idx % len(auto)])
            idx += 1
        if len(main) < 45:
            warnings.append(f"{cfg['name']}: deck incompleto ({len(main)}/45)")

    if not allow_over_45:
        main = main[:45]

    return PremadeBuild(
        deck=DeckBuildResult(main_deck=main, white_deck=white, innate_deck=innate),
        warnings=warnings,
    )


def export_test_decks(cards: list[CardDefinition], output_dir: str | Path) -> list[Path]:
    out = Path(output_dir)
    out.mkdir(parents=True, exist_ok=True)
    paths: list[Path] = []
    for religion in available_religions(cards):
        built = build_test_deck(cards, religion)
        payload = {
            "religion": religion,
            "main_deck_count": len(built.main_deck),
            "white_deck_count": len(built.white_deck),
            "main_deck": [c.name for c in built.main_deck],
            "white_deck": [c.name for c in built.white_deck],
        }
        path = out / f"{religion.replace(' ', '_')}.json"
        path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
        paths.append(path)
    return paths


reset_runtime_premades()

from __future__ import annotations

from holywar.effects.runtime import runtime_cards


WAVE8_CARDS = [
    "Larva Pestilenziale",
    "Manifestazione di Ph-Dak'Gaph",
    "Martire Esiliato",
    "Muninn",
    "Muschio Tossico",
    "Nefti",
    "Neith",
    "Occhi della Notte",
    "Osiride",
    "Paladino Corrotto",
    "Paladino della Fede",
    "Papa",
    "Pietra Focaia",
    "Pietra Levigata",
    "Prete Anziano",
    "Profanatore",
    "Sacerdote del Vuoto",
    "Sacerdote Orologio",
    "Sacerdote Oroscopo",
    "Schiavi",
    "Schiavo Mutilato",
    "Seth",
    "Sif",
    "Skadi",
    "Spirito dei Sepolti",
    "Stalagmiti",
    "Stalattiti",
    "Totem di Pietra",
    "Unut",
    "Vescovo della Città Buia",
    "Vescovo della Città Lucente",
    "Vucub.Came",
]


def _norm(name: str) -> str:
    import unicodedata

    value = unicodedata.normalize("NFKD", name)
    value = "".join(ch for ch in value if not unicodedata.combining(ch))
    return value.strip().lower()


def test_wave8_cards_are_scripted_with_on_play_actions() -> None:
    by_name = {k: v for k, v in runtime_cards._scripts.items()}  # noqa: SLF001 - contract test
    missing: list[str] = []
    bad_mode: list[str] = []
    no_actions: list[str] = []
    for name in WAVE8_CARDS:
        script = by_name.get(_norm(name))
        if script is None:
            missing.append(name)
            continue
        if str(script.on_play_mode).lower() != "scripted":
            bad_mode.append(name)
        if not script.on_play_actions:
            no_actions.append(name)
    assert missing == []
    assert bad_mode == []
    assert no_actions == []

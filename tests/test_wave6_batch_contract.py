from __future__ import annotations

from holywar.effects.runtime import runtime_cards


WAVE6_CARDS = [
    "Acqua",
    "Caverna Profonda",
    "Cenote Sacro",
    "Eco dei Morti",
    "Geroglifici",
    "Gggnag'ljep",
    "Incendio",
    "Libro di Ya-ner",
    "Pietre Aguzze",
    "Piramide: Chefren",
    "Piramide: Cheope",
    "Piramide: Micerino",
    "Rifugio Sacro",
    "Sabbie Mobili",
    "Segno Del Passato",
    "Umanità",
    "Vasi Canopi",
    "Biblioteca Apostolica",
    "Fiamma Primordiale",
    "Fiume dei Morti",
    "Ph'drna",
    "Sfinge",
    "Ciclicità Climatica",
    "Promessa dell'oltretomba",
    "Volere di Ph",
]


def _norm(name: str) -> str:
    import unicodedata

    value = unicodedata.normalize("NFKD", name)
    value = "".join(ch for ch in value if not unicodedata.combining(ch))
    return value.strip().lower()


def test_wave6_cards_are_scripted_with_on_play_actions() -> None:
    by_name = {k: v for k, v in runtime_cards._scripts.items()}  # noqa: SLF001 - contract test
    missing: list[str] = []
    bad_mode: list[str] = []
    no_actions: list[str] = []
    for name in WAVE6_CARDS:
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

from __future__ import annotations

from holywar.effects.runtime import runtime_cards


WAVE7_CARDS = [
    "Ah Puch",
    "Albero di Pietra",
    "Albero Sconsacrato",
    "Anfibio Tossico",
    "Anima Errante",
    "Anubi",
    "Aquila Vorace",
    "Araldo della Fine",
    "Atum",
    "Brigante",
    "Coccodrillo del Nilo",
    "Creature del Sottobosco",
    "Custode dei Sigilli",
    "Custode della Creazione",
    "Dio, il Creatore",
    "Fenrir",
    "Fujn-dar",
    "Geb",
    "Giorno 5: Creature del Mare",
    "Giorno 6: Creature di Terra",
    "Golem di Pietra",
    "Gub-ner Antico",
    "Guerriero Santificato",
    "Huginn",
    "Hun-Came",
    "Impostore",
    "Insetto Dorato",
    "Iside",
    "Ix Chel",
    "Jordh",
]


def _norm(name: str) -> str:
    import unicodedata

    value = unicodedata.normalize("NFKD", name)
    value = "".join(ch for ch in value if not unicodedata.combining(ch))
    return value.strip().lower()


def test_wave7_cards_are_scripted_with_on_play_actions() -> None:
    by_name = {k: v for k, v in runtime_cards._scripts.items()}  # noqa: SLF001 - contract test
    missing: list[str] = []
    bad_mode: list[str] = []
    no_actions: list[str] = []
    for name in WAVE7_CARDS:
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

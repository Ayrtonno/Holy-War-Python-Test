from __future__ import annotations

from holywar.effects.runtime import runtime_cards


WAVE3_CARDS = [
    "Concentrazione",
    "Meditazione",
    "Visione Celestiale",
    "Cronologia Sacra",
    "Offerta ai Sigilli",
    "Processione",
    "Sacrificio",
    "Tifone",
    "Avidità di Av",
    "Distorsione del Reliquiario",
    "Dono di Kah",
    "Paradosso di Ykknødar",
    "Pkad-nok'ljep",
    "Rito della Ri-Manifestazione",
    "Furia di Camazotz",
    "Resurrezione del Sacerdote",
    "Rituale dei Guardiani",
    "Giorno Festivo",
    "Veggente dell'Apocalisse",
    "Yggdrasil",
    "Nun",
    "Canti Religiosi",
    "Biblioteca d'Oro",
    "Faro di Alessandria",
    "Ptah",
    "Missionario",
    "Frammento dello Specchio",
    "Sussurro degli Antenati",
    "Ragnarok",
    "Terzo Sigillo: Carestia",
]


def _norm(name: str) -> str:
    import unicodedata

    value = unicodedata.normalize("NFKD", name)
    value = "".join(ch for ch in value if not unicodedata.combining(ch))
    return value.strip().lower()


def test_wave3_cards_are_scripted_with_on_play_actions() -> None:
    by_name = {k: v for k, v in runtime_cards._scripts.items()}  # noqa: SLF001 - contract test
    missing: list[str] = []
    bad_mode: list[str] = []
    no_actions: list[str] = []
    for name in WAVE3_CARDS:
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


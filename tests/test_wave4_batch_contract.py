from __future__ import annotations

from holywar.effects.runtime import runtime_cards


WAVE4_CARDS = [
    "Arca della Salvezza",
    "Bifrost",
    "Collasso",
    "Colori d'Autunno",
    "Diboscamento",
    "Elemosina",
    "Furia di Llakhnal",
    "Giorno 3: Terre e Mari",
    "Giorno 7: Riposo",
    "Giudizio Universale",
    "Inverno",
    "Maledizione di Xibalba",
    "Maledizione di Ykknødar",
    "Muraglia",
    "Pellegrinaggio Forzato",
    "Piaga Ignota",
    "Pioggia Acida",
    "Pietra Nera",
    "Pietre Pesanti",
    "Pozione Perdi-tempo",
    "Proibizione Cristiana",
    "Proibizione di Ph",
    "Proibizione Egizia",
    "Proibizione Naturale",
    "Quarto Sigillo: Morte",
    "Ritorno Infame",
    "Sacrificio del Tempo",
    "Secondo Sigillo: Guerra",
    "Tempesta",
    "Tempesta di Sabbia",
    "Terremoto: Magnitudo 3",
    "Tornado",
    "Uragano",
    "Vilipendio",
    "Voragine",
]


def _norm(name: str) -> str:
    import unicodedata

    value = unicodedata.normalize("NFKD", name)
    value = "".join(ch for ch in value if not unicodedata.combining(ch))
    return value.strip().lower()


def test_wave4_cards_are_scripted_with_on_play_actions() -> None:
    by_name = {k: v for k, v in runtime_cards._scripts.items()}  # noqa: SLF001 - contract test
    missing: list[str] = []
    bad_mode: list[str] = []
    no_actions: list[str] = []
    for name in WAVE4_CARDS:
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

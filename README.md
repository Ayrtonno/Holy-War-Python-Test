# Holy War

Holy War in Python con GUI e motore a script carta-per-carta.

## Setup

```powershell
py -3.14 -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -e .[dev]
```

## Avvio

```powershell
.\.venv\Scripts\python.exe -m holywar.gui --cards-json "holywar/data/cards.json"
```

Se vuoi usare deck premade custom, aggiungi `--premades-json "my_premades.json"` al comando.

Controlli GUI principali:
- Tasto destro su carta in mano: menu contestuale di gioco (Attacco/Difesa/target)
- Tasto destro su tuo Santo in attacco: menu `Attacca` + `Attiva abilita`
- Tasto destro su slot tuo (difesa/artefatto/edificio): `Attiva abilita`
- Bottone `Fine Turno`, `Salva`, `Esporta Log`
- Selettori `Deck P1` / `Deck P2`: scegli `AUTO (test)` o un deck premade della religione selezionata

## Funzionalita MVP

- Modalita `1v1 locale` e `vs AI`
- Deck test deterministici per ogni religione (niente deck casuali)
- Deck premade selezionabili per religione nella GUI
- Meccaniche core: pesca, ispirazione, mano max 8, campo attacco/difesa, attacchi, peccato, cimitero, scomunica, token
- Effetti implementati carta per carta tramite script
- Salvataggio/caricamento partita in JSON
- Log partita esportabile in file testo
- Test automatici con `pytest`

## Architettura Effetti

- `holywar/effects/library.py`: dispatcher leggero
- `holywar/effects/registry.py`: registry handler per carta (`register_play`, `register_enter`)
- `holywar/effects/card_scripts/cards/...`: script per carta, uno per file
- `holywar/effects/cards/...`: moduli legacy ancora presenti solo per compatibilita interna

## Note

Il motore usa nomi/variabili in inglese e testi output in italiano.

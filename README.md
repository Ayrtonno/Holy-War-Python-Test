# Holy War (Terminal MVP)

MVP del gioco Holy War in Python da terminale.

## Setup

```powershell
py -3.14 -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -e .[dev]
```

## Avvio

```powershell
holywar --deck-xlsx "E:\Script HW\Holy War.xlsx"
```

Import deck premade custom da JSON:

```powershell
holywar --cards-json "holywar/data/cards.json" --premades-json "my_premades.json"
```

Export deck premade (base) in JSON modificabile:

```powershell
holywar --export-premades-json "my_premades.json"
```

## Avvio GUI

```powershell
python -m holywar.gui --deck-xlsx "E:\Script HW\Holy War.xlsx"
```

Oppure, dopo `pip install -e .[dev]`:

```powershell
holywar-gui --cards-json "holywar/data/cards.json"
```

Con premade custom:

```powershell
holywar-gui --cards-json "holywar/data/cards.json" --premades-json "my_premades.json"
```

Controlli GUI principali:
- Tasto destro su carta in mano: menu contestuale di gioco (Attacco/Difesa/target)
- Tasto destro su tuo Santo in attacco: menu `Attacca` + `Attiva abilita`
- Tasto destro su slot tuo (difesa/artefatto/edificio): `Attiva abilita`
- Bottone `Fine Turno`, `Salva`, `Esporta Log`
- Selettori `Deck P1` / `Deck P2`: scegli `AUTO (test)` o un deck premade della religione selezionata

## Funzionalita MVP

- Modalita `1v1 locale` e `vs AI`
- Deck test deterministici per ogni religione (niente deck casuali)
- Deck premade selezionabili per religione (CLI e GUI)
- Meccaniche core: pesca, ispirazione, mano max 8, campo attacco/difesa, attacchi, peccato, cimitero, scomunica, token
- Effetti implementati per un set iniziale di carte
- Salvataggio/caricamento partita in JSON
- Log partita esportabile in file testo
- Test automatici con `pytest`

## Architettura Effetti

- `holywar/effects/library.py`: dispatcher leggero
- `holywar/effects/registry.py`: registry handler per carta (`register_play`, `register_enter`)
- `holywar/effects/cards/...`: modulo per carta (Animismo/Norrena gia scaffoldati, un file per carta)
- `holywar/effects/legacy_handlers.py`: fallback compatibilita con logica pre-refactor

## Note

Il motore usa nomi/variabili in inglese e testi output in italiano.

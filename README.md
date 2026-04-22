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

I deck creati/modificati da GUI vengono salvati in:
- Windows: `%APPDATA%\HolyWar\premade_decks.json`

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

## Installer Windows (.exe setup)

Prerequisiti:
- Inno Setup 6 installato (`ISCC.exe`)
- venv attiva con dipendenze (`pip install -e .[dev]`)

Comando completo (build exe + setup installer):

```powershell
.\scripts\build_installer.ps1 -Version 0.1.0
```

Comando rapido (se hai gia `dist\HolyWar` e vuoi solo rigenerare il setup):

```powershell
.\scripts\build_installer.ps1 -Version 0.1.0 -SkipPyInstaller
```

Cosa fa lo script:
- compila l'app GUI con PyInstaller in `dist\HolyWar\`
- compila l'installer Inno Setup usando `installer\HolyWar.iss`

Output finale:
- `installer\dist\HolyWar-Setup-<version>.exe`

L'installer crea:
- installazione in `Program Files\Holy War`
- shortcut menu Start
- shortcut desktop (opzionale)
- disinstallazione standard Windows

La disinstallazione rimuove anche:
- `%APPDATA%\HolyWar`
- `%LOCALAPPDATA%\HolyWar`
- `%LOCALAPPDATA%\Temp\HolyWar`

Se l'app installata non parte:
- controlla il log `%APPDATA%\HolyWar\startup_error.log`

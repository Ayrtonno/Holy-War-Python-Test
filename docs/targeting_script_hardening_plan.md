# Piano Di Rafforzamento Script/Targeting (Universale)

## Obiettivo
- Rendere il target picking deterministico, coerente e robusto su tutte le carte.
- Eliminare ambiguità tra effetti opzionali e requisiti/costi obbligatori.
- Ridurre bug futuri con pipeline unica, micro-azioni standard, lint e test regressivi.

## Principio Chiave
Le carte simili nel testo possono avere comportamento diverso in base alla policy del target.
La policy deve essere esplicita in ogni step con bersaglio.

## Contratto Universale Del Target
Ogni step con target deve dichiarare:
- `target_policy`: `optional_resolve | required_to_activate | required_to_resolve`
- `selection_mode`: `none | auto | prompt`
- `min_targets`, `max_targets`
- `cancel_behavior`: `noop | abort_step | abort_action`
- `allow_none`: coerente con policy

Regole globali:
1. `optional_resolve`
- Se pool candidati = 0: non aprire prompt, step saltato pulito.
- Se pool > 0: aprire prompt con soli candidati validi.
- Cancel: annulla solo lo step (`abort_step`).

2. `required_to_activate`
- Se pool = 0: azione illegale (non giocabile/non attivabile).
- Se pool > 0: prompt obbligatorio.
- Cancel: annulla attivazione/giocata completa (`abort_action`).

3. `required_to_resolve`
- La carta può essere giocata/attivata.
- Se al resolve non ci sono candidati: lo step fizzla.
- Se prompt aperto e cancel: annulla lo step o la risoluzione in base al `cancel_behavior` dichiarato.

Regole anti-bug:
- Nessun doppio prompt per step consumer (`selected_target(s)` dopo `choose_targets`).
- Candidati sempre filtrati, deduplicati, ordinati in modo stabile.
- Ogni prompt deve avere log tecnico su apertura/non apertura e motivo.

## Pipeline Unica Di Risoluzione Effetti
Tutte le carte devono usare lo stesso ciclo:
1. `precheck`
- requisiti statici
- usage limits
- validazione `required_to_activate`

2. `collect_choices`
- ordine fisso: `choose_option` -> `choose_targets` -> `choose_slot`
- risultati salvati in `resolution_context` immutabile

3. `commit_costs`
- consumare costi solo dopo scelta valida
- in caso di cancel/fail: rollback pulito

4. `apply_effects`
- applicare micro-azioni atomiche parametrizzate

5. `post_events`
- ordine eventi fisso e documentato

6. `finalize`
- cleanup flags temporanee
- verifica invarianti stato

## Libreria Di Micro-Azioni Standard
Evitare logica ad hoc nelle singole carte.

Set base consigliato:
- `choose_targets`
- `choose_option`
- `choose_slot_for_summon`
- `move_selected_to_hand`
- `summon_selected_to_field`
- `destroy_selected`
- `draw_n`
- `discard_prompt`
- `apply_buff`
- `if/else` (branching dichiarativo)

## Esempi Canonici (Da Mantenere Invariati)

### Caso A: Recupero opzionale dal cimitero
Testo esempio: “Scegli una carta nel cimitero e portala nella tua mano.”
- Policy: `optional_resolve`
- Se cimitero vuoto: nessun prompt, effetto termina.
- Se cimitero non vuoto: prompt target.
- Dopo OK: risoluzione effetto.

### Caso B: Costo obbligatorio dal cimitero
Testo esempio: “Può essere giocata solo scomunicando una carta dal tuo cimitero.”
- Policy: `required_to_activate`
- Se cimitero vuoto: non attivabile/non giocabile.
- Se cimitero non vuoto: prompt obbligatorio.
- Cancel prompt: annulla l’azione.
- Selezione valida + OK: effetto prosegue.

## Linter Statico Obbligatorio (Pre-Runtime)
Errori bloccanti:
- consumer `selected_target(s)` senza producer `choose_targets`
- `required_to_activate` con `allow_none=true`
- `min_targets>0` con `selection_mode=none`
- target usati in branch senza dichiarazione
- conflitti tra producer multipli nello stesso context key

Warning:
- condizioni duplicate/ridondanti
- filtri troppo generici
- side effects prima di `commit_costs`

Output linter:
- per-carta
- severità
- step coinvolto
- fix suggerito

## Test Regressivi Universali
Per ogni carta con target:
1. pool vuoto
2. pool con 1 target
3. pool con N target
4. cancel prompt
5. target non più valido al resolve
6. catena multi-step (`choose_option` + `choose_targets` + slot)

Regola progetto:
- ogni bug fix deve aggiungere test regressione permanente.
- nessuna carta nuova senza matrice test minima.

## Osservabilità / Debug
- Trace strutturato per step: policy, pool, prompt, cancel, risultato.
- Overlay debug GUI opzionale con motivo esclusione candidati.
- Replay deterministico con seed + scelte.

## Piano Di Esecuzione (Sprint)

### Sprint 1: Fondazione
- introdurre `target_policy` nel runtime
- centralizzare gate apertura prompt
- consolidare picker slot summon con policy unica
- trace minimo

### Sprint 2: Sicurezza
- linter bloccante
- harness test targeting
- migrazione/fix carte critiche (Ba Xian e simili)

### Sprint 3: Scalabilità
- migrazione batch per famiglie meccaniche
- rimozione path legacy duplicati
- standardizzazione branch effect

### Sprint 4: Audit totale
- revisione 300+ carte
- report coverage policy/test per carta
- merge gate: linter + test verdi obbligatori

## Criteri Di Accettazione Finali
1. Nessun prompt quando pool=0 in `optional_resolve`.
2. Nessuna attivazione possibile con pool=0 in `required_to_activate`.
3. Cancel gestito coerentemente senza side effects parziali.
4. Nessun doppio prompt non previsto.
5. Suite regressiva verde sulle carte target-based.
6. Linter senza errori sull’intero catalogo.

## Nota Operativa
Prima priorità assoluta: target picking.
Seconda priorità: pipeline e micro-azioni.
Terza priorità: audit massivo e validazione automatica.

## TODO Aggiuntivo: Unificazione Trigger/Attivazioni/Summoning Con Evento Canonico

Problema rilevato:
- Attivazioni e summon dipendono oggi da molti eventi/flag/condizioni distribuiti.
- Troppa logica ad hoc per differenziare "da dove parte", "dove arriva", "causa" e "tipo carta".

Obiettivo:
- Ridurre branching manuale e convergere su un dispatcher unico, dichiarativo e testabile.

### Strategia
1. Introdurre un evento canonico di transizione carta: `on_zone_change`.
2. Far passare ogni spostamento reale attraverso questo evento (mano->campo, cimitero->mano, campo->cimitero, deck->mano, ecc.).
3. Esprimere i trigger con blocchi dichiarativi (`when/if/do`) invece di if sparsi nel codice.

### Payload Standard Minimo Di `on_zone_change`
- `card_uid`, `card_name`, `card_type`
- `owner`
- `controller_before`, `controller_after`
- `from_zone`, `to_zone`
- `from_slot`, `to_slot`
- `cause` (`play`, `effect`, `battle`, `cost`, `draw`, `discard`, ...)
- `source_uid` (carta/effetto origine)
- `turn`, `phase`

### Filtri Trigger Da Supportare (Generici)
- `from_zone_in`
- `to_zone_in`
- `card_type_in`
- `card_filter` (name equals/contains/tag)
- `owner_is` / `controller_is`
- `cause_in`
- `source_is_self` / `source_is_other`
- `frequency` (`each_time`, `each_turn`, `once_per_game`)

### Benefici Attesi
- Regole uniformi per: "entra in campo", "solo se arriva al cimitero", "solo se parte dalla mano", ecc.
- Meno duplicazioni e minore rischio doppio trigger/doppio prompt.
- Maggiore leggibilità degli script e più facilità nell'introdurre nuove carte.

### Piano Implementativo Incrementale
1. Aggiungere `on_zone_change` in parallelo agli eventi legacy.
2. Introdurre `TriggerMatcher` unico (match filtri + frequency).
3. Migrare prima le famiglie a rischio alto (Ba Xian/summon/revive/discard).
4. Aggiungere regression test su matrice transizioni (`from/to/cause`).
5. Deprecare progressivamente i path legacy ridondanti.

### Criteri Di Accettazione Specifici
1. Ogni movimento carta importante genera un `on_zone_change` coerente.
2. Trigger equivalenti non dipendono più da codice ad hoc in più punti.
3. Nessun doppio trigger su singola transizione.
4. Suite test transizioni verde su carte critiche.

## TODO Aggiuntivo: Positioning, Trigger Automatici, Effetti "PUOI" e Branch Condizionali

Problema rilevato:
- La logica tra piazzamento (slot/zona), trigger automatici obbligatori e trigger opzionali ("PUOI") non è centralizzata.
- I branch condizionali ("se Y allora X, altrimenti Z") sono spesso gestiti in modo non uniforme.

Obiettivo:
- Uniformare il comportamento senza riscrivere tutte le carte da zero.
- Introdurre regole canoniche per quando un effetto parte automaticamente, quando richiede conferma e come risolvere i branch.

### 1) Positioning Canonico
Ogni azione che piazza carte sul campo deve passare da un unico blocco di policy:
- `placement_policy`: `auto_first_free | prompt_slot_required | prompt_slot_optional`
- `allowed_zones`: es. `attack/defense` o `artifact` o `building`
- `fallback_policy`: `fail | first_free | skip_step`

Regole:
1. Se la carta/effetto richiede scelta locazione: prompt sempre (`prompt_slot_required`).
2. Se il testo non richiede scelta: policy esplicita nello script (`auto_first_free` o altro).
3. Nessun piazzamento deve bypassare il resolver centrale slot/zone.

### 2) Trigger Automatici Obbligatori vs Opzionali ("PUOI")
Introdurre campo esplicito su trigger/action:
- `activation_mode`: `mandatory_auto | optional_prompt | optional_silent`

Semantica:
1. `mandatory_auto`
- Se condizioni vere, si risolve automaticamente senza chiedere conferma.
- Se richiede target, usa la target policy definita (required/optional).

2. `optional_prompt` (tipico "PUOI")
- Se condizioni vere, mostra prompt SI/NO all'operatore.
- Se NO: nessun effetto e nessun costo.
- Se SI: parte il flow normale (target/slot/costi/resolve).

3. `optional_silent`
- Per casi AI/automazioni in cui la scelta è interna, senza popup utente.

### 3) Branch Condizionali Canonici
Standardizzare i branch con struttura unica:
- `if` / `elif` / `else` dichiarativi
- ordine di valutazione deterministico
- short-circuit esplicito

Regole:
1. Valutare condizioni in ordine scritto.
2. Eseguire solo il primo branch valido, salvo flag `allow_multi_branch=true`.
3. Ogni branch dichiara separatamente target/costi/azioni.
4. Vietato condividere stato implicito ambiguo tra branch (solo context esplicito).

### 4) Compatibilità Incrementale (No Rewrite Totale)
- Mantenere adapter legacy per script esistenti.
- Migrare per famiglie di carte (batch), non one-shot globale.
- Introdurre lint con warning iniziali e poi errori bloccanti a maturità.

### 5) Test Minimi Obbligatori Per Ogni Carta Migrata
1. Trigger mandatory auto in condizione vera/falsa.
2. Trigger optional ("PUOI") con scelta SI e scelta NO.
3. Branch condition: percorso principale e fallback.
4. Positioning: slot valido/non valido, cancel prompt, fallback policy.

### 6) Criteri Di Accettazione Specifici
1. Nessun effetto "PUOI" si auto-attiva senza consenso quando è richiesto prompt.
2. Nessun effetto mandatory resta in attesa di prompt non previsto.
3. Branch condizionali ripetibili con stesso esito a parità di stato.
4. Positioning coerente con policy dichiarata su tutte le azioni di summon/place.

## TODO Aggiuntivo: Regola Globale Su Positioning In Campo

Regola di progetto (default universale):
- Il posizionamento sul terreno/campo deve essere scelto dal player quasi sempre.
- `prompt_slot_required` è il default globale per summon/place su slot di campo.
- Auto-posizionamento consentito solo se il testo carta/effetto specifica esplicitamente dove e come posizionare.

Semantica operativa:
1. Default engine/script: `placement_policy=prompt_slot_required`.
2. Override verso auto-placement solo con dichiarazione esplicita nello script:
- es. `placement_policy=auto_first_free` oppure `fixed_zone=fixed_slot`.
3. Se la carta specifica una posizione precisa (es. "in Difesa", "in Attacco 1"):
- nessun prompt, posizionamento deterministico secondo testo.
4. Se lo script non specifica posizione e ci sono slot validi:
- prompt obbligatorio al player.
5. Se non ci sono slot validi:
- effetto fallisce/skip secondo policy dichiarata, con log esplicito.

Controlli anti-regressione:
- Test automatico che fallisce se uno `summon_target_to_field` usa first-free senza override esplicito.
- Linter: warning/error su azioni di placement senza policy dichiarata.

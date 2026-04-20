from __future__ import annotations

# Deck premade forniti dall'utente.
# Ogni entry: (nome carta, copie)

PREMADE_DECKS: dict[str, dict] = {
    # Cristianesimo
    "cristianesimo_sette_sigilli": {
        "religion": "Cristianesimo",
        "name": "I Sette Sigilli dell'Apocalisse",
        "cards": [
            ("Altare dei Sette Sigilli", 1), ("Primo Sigillo", 3), ("Offerta ai Sigilli", 2),
            ("Custode dei Sigilli", 3), ("Araldo della Fine", 3), ("Veggente dell'Apocalisse", 1),
            ("Quarto Sigillo: Morte", 1), ("Secondo Sigillo: Guerra", 2), ("Terzo Sigillo: Carestia", 2),
            ("Settimo Sigillo: Apocalisse", 1), ("Trombe del Giudizio", 1), ("Preghiera", 2),
            ("Sacri Vasi", 1), ("Perdono", 2), ("Cura", 3), ("Moribondo", 3), ("Seguace", 3),
        ],
    },
    "test_giocatore": {
        "religion": "Animismo",
        "name": "TEST PLAYER",
        "cards": [
            ("Processione", 5), ("Albero Fortunato", 5), ("Radici", 5), ("Ritorno Catastrofico", 10),
        ],
    },
    "test_nemico": {
        "religion": "Animismo",
        "name": "TEST NEMICO",
        "cards": [
            ("Albero Fortunato", 3)
        ],
    },
    "cristianesimo_via_martirio": {
        "religion": "Cristianesimo",
        "name": "La Via del Martirio",
        "cards": [
            ("Brigante", 3), ("Moribondo", 3), ("Ascensione", 2), ("Sacrificio", 4),
            ("Martire Esiliato", 3), ("Prete Anziano", 3), ("Chiesa", 1), ("Canti Religiosi", 2),
            ("Umanità", 2), ("Paladino della Fede", 2), ("Guerriero Santificato", 2),
            ("Elemosina", 1), ("Cronologia Sacra", 1), ("Seguace", 2), ("Cura Rapida", 3),
        ],
    },
    "cristianesimo_genesi_assoluto": {
        "religion": "Cristianesimo",
        "name": "Genesi dell'Assoluto",
        "cards": [
            ("Custode della Creazione", 1), ("Genesi: Compimento", 1), ("Giorno 1: Cieli e Terra", 1),
            ("Giorno 2: Cielo Terrestre", 1), ("Giorno 3: Terre e Mari", 1), ("Giorno 4: Stelle", 1),
            ("Giorno 5: Creature del Mare", 1), ("Giorno 6: Creature di Terra", 1), ("Giorno 7: Riposo", 1),
            ("Settimo Sigillo", 1), ("Veggenza", 2), ("Processione", 3), ("Biblioteca Apostolica", 1),
            ("Perdono", 2), ("Preghiera", 2), ("Moribondo", 3), ("Concentrazione", 3),
        ],
    },

    # Norrena
    "norrena_trono_asgard": {
        "religion": "Mitologia Norrena",
        "name": "Il Trono di Asgard",
        "cards": [
            ("Odino", 1), ("Thor", 1), ("Tanngnjostr", 2), ("Tanngrisnir", 2), ("Gungnir", 1),
            ("Megingjörð", 1), ("Járngreipr", 1), ("Mjolnir", 1), ("Huginn", 2), ("Muninn", 2),
            ("Valhalla", 1), ("Yggdrasil", 1), ("Figli di Odino", 3), ("Saga degli Eroi Caduti", 2),
            ("Concentrazione", 2),
        ],
    },
    "norrena_crepuscolo_giganti": {
        "religion": "Mitologia Norrena",
        "name": "Il Crepuscolo dei Giganti",
        "cards": [
            ("Fenrir", 1), ("Jormungandr", 1), ("Loki", 2), ("Assalto Invernale", 2), ("Ragnarok", 1),
            ("Skadi", 2), ("Tempesta di Asgard", 2), ("Bifrost", 2), ("Seguace", 3), ("Moribondo", 3), ("Cura", 2),
        ],
    },
    "norrena_custodi_yggdrasil": {
        "religion": "Mitologia Norrena",
        "name": "I Custodi di Yggdrasil",
        "cards": [
            ("Yggdrasil", 1), ("Valhalla", 1), ("Huginn", 3), ("Muninn", 3), ("Sif", 3), ("Jordh", 2),
            ("Saga degli Eroi Caduti", 2), ("Concentrazione", 3), ("Meditazione", 2), ("Ricerca Archeologica", 1),
            ("Cura Rapida", 2),
        ],
    },

    # Animismo
    "animismo_respiro_antico_albero": {
        "religion": "Animismo",
        "name": "Il Respiro dell'Antico Albero",
        "cards": [
            ("Albero Sacro", 1), ("Ruscello Sacro", 1), ("Cuore della foresta", 2), ("Corteccia", 2),
            ("Radici", 2), ("Preghiera: Fertilità", 1), ("Albero Fortunato", 3), ("Albero Secolare", 1),
            ("Foresta Sacra", 1), ("Pioggia", 3),
        ],
    },
    "animismo_cataclisma_elementale": {
        "religion": "Animismo",
        "name": "Il Cataclisma Elementale",
        "cards": [
            ("Fiamma Primordiale", 1), ("Incendio", 3), ("Vulcano", 1), ("Terremoto: Magnitudo 10", 1),
            ("Uragano", 1), ("Tornado", 1), ("Tempesta", 3), ("Pioggia Acida", 3), ("Voragine", 2),
            ("Cataclisma Ciclico", 1),
        ],
    },
    "animismo_risveglio_pietre": {
        "religion": "Animismo",
        "name": "Il Risveglio delle Pietre",
        "cards": [
            ("Albero di Pietra", 3), ("Golem di Pietra", 3), ("Caverna Profonda", 3), ("Memoria della Pietra", 2),
            ("Pietra Focaia", 2), ("Stalagmiti", 3), ("Stalattiti", 3), ("Legame Primordiale", 2),
        ],
    },

    # Egizie
    "egizie_trinita_faraoni": {
        "religion": "Egiziane",
        "name": "La Trinità dei Faraoni",
        "cards": [
            ("Osiride", 1), ("Iside", 2), ("Set", 2), ("Seth", 1), ("Piramide: Cheope", 1),
            ("Piramide: Chefren", 1), ("Piramide: Micerino", 1), ("Sfinge", 1), ("Vasi Canopi", 2),
            ("Mummificazione", 2),
        ],
    },
    "egizie_passaggio_aldila": {
        "religion": "Egiziane",
        "name": "Il Passaggio nell'Aldilà",
        "cards": [
            ("Anubi", 1), ("Nefti", 3), ("Passaggio all'Aldilà", 3), ("Ultima Offerta", 2), ("Rito Funebre", 2),
            ("Medicina Egizia", 2), ("Bende Consacrate", 3),
        ],
    },
    "egizie_furia_nilo": {
        "religion": "Egiziane",
        "name": "La Furia del Nilo",
        "cards": [
            ("Coccodrillo del Nilo", 3), ("Schiavo Mutilato", 3), ("Schiavi", 3), ("Ra", 1), ("Nun", 1),
            ("Tempesta di Sabbia", 2), ("Piaga Ignota", 2),
        ],
    },

    # Ph-Dak'Gaph
    "phdk_silenzio_abisso": {
        "religion": "Ph-DakGaph",
        "name": "Il Silenzio dell'Abisso",
        "cards": [
            ("Manifestazione di Ph-Dak'Gaph", 1), ("Paradosso di Ykknødar", 2), ("Maledizione di Ykknødar", 1),
            ("Specchio di Ykknødar", 1), ("Frammento dello Specchio", 3), ("Rito della Ri-Manifestazione", 2),
            ("Risveglio di Ph-Dak'Gaph", 1), ("Sacerdote del Vuoto", 3),
        ],
    },
    "phdk_culto_gubner": {
        "religion": "Ph-DakGaph",
        "name": "Il Culto dei Gub-ner",
        "cards": [
            ("Ya-ner", 3), ("Libro di Ya-ner", 2), ("Gub-ner Antico", 2), ("Token Gub-ner", 5),
            ("Av'drna", 2), ("Dono di Kah", 3), ("Fujn'lyat", 2),
        ],
    },
    "phdk_caos_primordiale": {
        "religion": "Ph-DakGaph",
        "name": "Il Caos Primordiale",
        "cards": [
            ("Llakhnal", 3), ("Pkad-nok", 3), ("Kah-ok", 3), ("Furia di Llakhnal", 2),
            ("Avidità di Av", 2), ("Ph'kdam", 1), ("Distorsione del Reliquiario", 2),
        ],
    },

    # Cristianesimo - Set B
    "cristianesimo_b1_sigilli_martirio": {
        "religion": "Cristianesimo",
        "name": "B1 - Sigilli e Martirio",
        "cards": [
            ("Prete Anziano", 3), ("Moribondo", 2), ("Paladino della Fede", 3), ("Custode dei Sigilli", 3),
            ("Guerriero Santificato", 2), ("Frate Curatore", 2), ("Primo Sigillo", 3), ("Offerta ai Sigilli", 3),
            ("Secondo Sigillo: Guerra", 3), ("Preghiera", 3), ("Perdono", 3), ("Processione", 3),
            ("Proibizione Cristiana", 2), ("Altare dei Sette Sigilli", 1), ("Veggente dell'Apocalisse", 1),
            ("Papa", 1), ("Trombe del Giudizio", 1), ("Quarto Sigillo: Morte", 1), ("Settimo Sigillo", 1),
            ("Arca della salvezza", 1), ("Terzo Sigillo: Carestia", 1), ("Araldo della Fine", 1), ("Giorno Festivo", 1),
        ],
    },
    "cristianesimo_b2_genesi": {
        "religion": "Cristianesimo",
        "name": "B2 - Genesi Estesa",
        "cards": [
            ("Impostore", 3), ("Moribondo", 3), ("Prete Anziano", 3), ("Giorno 5: Creature del Mare", 3),
            ("Giorno 6: Creature di Terra", 3), ("Paladino della Fede", 3), ("Processione", 3), ("Sacrificio", 4),
            ("Preghiera", 3), ("Veggenza", 3), ("Giorno Festivo", 2), ("Giorno 1: Cieli e Terra", 1),
            ("Giorno 2: Cielo Terrestre", 1), ("Giorno 3: Terre e Mari", 1), ("Giorno 4: Stelle", 1),
            ("Giorno 7: Riposo", 1), ("Settimo Sigillo", 1), ("Cronologia Sacra", 1), ("Biblioteca d'Oro", 2),
            ("Custode della Creazione", 1), ("Genesi: Compimento", 1), ("Ascensione", 1),
        ],
    },
    "cristianesimo_b3_creatore": {
        "religion": "Cristianesimo",
        "name": "B3 - Via del Creatore",
        "cards": [
            ("Missionario", 3), ("Paladino della Fede", 3), ("Guerriero Santificato", 3), ("Frate Curatore", 3),
            ("Vescovo della Città Lucente", 2), ("Brigante", 2), ("Preghiera", 3), ("Ascensione", 3),
            ("Sacrificio", 3), ("Perdono", 2), ("Veggenza", 2), ("Acqua", 1), ("Aria", 1), ("Fuoco", 1), ("Terra", 1),
            ("Umanità", 2), ("Rifugio Sacro", 2), ("Canti Religiosi", 2), ("Dio, il Creatore", 1), ("Chiesa", 1),
            ("Biblioteca Apostolica", 1), ("Campana", 1), ("Sacri Vasi", 1), ("Giudizio Universale", 1),
        ],
    },

    # Animismo - Set B
    "animismo_b1_antico_albero": {
        "religion": "Animismo",
        "name": "B1 - Antico Albero",
        "cards": [
            ("Albero Fortunato", 3), ("Pianta Carnivora", 3), ("Albero Sconsacrato", 3), ("Creature del Sottobosco", 3),
            ("Albero di Pietra", 3), ("Insetto della Palude", 3), ("Muschio Tossico", 3), ("Pietra Bianca", 3),
            ("Pioggia", 3), ("Proibizione Naturale", 3), ("Corteccia", 3), ("Cuore della foresta", 3), ("Radici", 3),
            ("Albero Sacro", 1), ("Albero Secolare", 1), ("Foresta Sacra", 1), ("Ruscello Sacro", 1),
            ("Preghiera: Fertilità", 1), ("Fioritura Primaverile", 1),
        ],
    },
    "animismo_b2_pietre": {
        "religion": "Animismo",
        "name": "B2 - Rocce e Totem",
        "cards": [
            ("Insetto della Palude", 3), ("Occhi della Notte", 3), ("Stalagmiti", 3), ("Stalattiti", 3),
            ("Golem di Pietra", 3), ("Pietra Focaia", 3), ("Totem di Pietra", 3), ("Albero di Pietra", 2),
            ("Memoria della Pietra", 3), ("Pietra Bianca", 3), ("Pietra Nera", 3), ("Pietre Pesanti", 3),
            ("Caverna Profonda", 3), ("Pietre Aguzze", 3), ("Sabbie Mobili", 2), ("Pietra Levigata", 1),
            ("Segno Del Passato", 1),
        ],
    },
    "animismo_b3_cataclismi": {
        "religion": "Animismo",
        "name": "B3 - Tempeste e Cataclismi",
        "cards": [
            ("Larva Pestilenziale", 3), ("Insetto Dorato", 3), ("Anfibio Tossico", 3), ("Occhi della Notte", 3),
            ("Albero Fortunato", 2), ("Pioggia Acida", 3), ("Tempesta", 3), ("Monsone", 3), ("Voragine", 3),
            ("Tifone", 3), ("Diboscamento", 2), ("Terremoto: Magnitudo 3", 2), ("Uragano", 1), ("Inverno", 1),
            ("Tornado", 1), ("Cataclisma Ciclico", 1), ("Fiamma Primordiale", 1), ("Incendio", 3), ("Sequoia", 1),
            ("Aquila Vorace", 1), ("Sacrificio Naturale", 2),
        ],
    },

    # Egiziane - Set B
    "egizie_b1_aldila_ordine": {
        "religion": "Egiziane",
        "name": "B1 - Aldilà Ordinato",
        "cards": [
            ("Nefti", 3), ("Set", 3), ("Deriu-hebet", 3), ("Ptah", 3), ("Geb", 3), ("Sacerdote Oroscopo", 3),
            ("Passaggio all'Aldilà", 3), ("Mummificazione", 3), ("Bende Consacrate", 3), ("Proibizione Egizia", 3),
            ("Rito Funebre", 3), ("Ultima Offerta", 2), ("Coccodrillo del Nilo", 2), ("Seth", 2), ("Iside", 1),
            ("Osiride", 1), ("Anubi", 1), ("Vasi Canopi", 2), ("Nun", 1),
        ],
    },
    "egizie_b2_piramidi": {
        "religion": "Egiziane",
        "name": "B2 - Le Tre Piramidi",
        "cards": [
            ("Nefti", 3), ("Set", 3), ("Deriu-hebet", 3), ("Neith", 3), ("Geb", 3), ("Ptah", 3),
            ("Sacerdote Orologio", 3), ("Schiavo Mutilato", 3), ("Passaggio all'Aldilà", 3), ("Proibizione Egizia", 3),
            ("Bende Consacrate", 2), ("Ultima Offerta", 2), ("Piramide: Chefren", 1), ("Piramide: Cheope", 1),
            ("Piramide: Micerino", 1), ("Nun", 1), ("Ra", 1), ("Sfinge", 1), ("Esondazione del Nilo", 1),
            ("Faro di Alessandria", 2), ("Tempesta di Sabbia", 1), ("Piaga Ignota", 1),
        ],
    },
    "egizie_b3_riti_totali": {
        "religion": "Egiziane",
        "name": "B3 - Riti Totali",
        "cards": [
            ("Set", 3), ("Nefti", 3), ("Deriu-hebet", 3), ("Neith", 3), ("Geb", 3), ("Ptah", 3),
            ("Sacerdote Orologio", 3), ("Sacerdote Oroscopo", 3), ("Unut", 3), ("Schiavi", 3),
            ("Coccodrillo del Nilo", 3), ("Bende Consacrate", 3), ("Passaggio all'Aldilà", 3), ("Mummificazione", 3),
            ("Atum", 1), ("Faro di Alessandria", 1), ("Medicina Egizia", 1),
        ],
    },

    # Ombre Maya / Xibalba - Set B
    "xibalba_b1_guardiani": {
        "religion": "Ombre Maya",
        "name": "B1 - Guardiani dell'Oltretomba",
        "cards": [
            ("Anima Errante", 3), ("Ix Chel", 3), ("Spirito dei Sepolti", 3), ("Sussurro degli Antenati", 3),
            ("Sacrificio della Fertilità", 3), ("Cenote Sacro", 3), ("Eco dei Morti", 3), ("Fiume dei Morti", 3),
            ("Calice Insanguinato", 3), ("Tikal", 3), ("Concentrazione", 3), ("Cura", 2), ("Ritorno Infame", 3),
            ("Vucub.Came", 1), ("Hun-Came", 1), ("Camazotz", 1), ("Ah Puch", 1), ("Rituale dei Guardiani", 1),
            ("Rituale Sepolcrale", 1), ("Promessa dell'oltretomba", 1),
        ],
    },
    "xibalba_b2_maledizione": {
        "religion": "Ombre Maya",
        "name": "B2 - Maledizione di Xibalba",
        "cards": [
            ("Anima Errante", 3), ("Ix Chel", 3), ("Spirito dei Sepolti", 3), ("Sussurro degli Antenati", 3),
            ("Furia di Camazotz", 3), ("Cenote Sacro", 3), ("Eco dei Morti", 3), ("Fiume dei Morti", 3),
            ("Calice Insanguinato", 3), ("Tikal", 3), ("Concentrazione", 3), ("Meditazione", 2), ("Corruzione", 3),
            ("Vucub.Came", 1), ("Hun-Came", 1), ("Camazotz", 1), ("Maledizione di Xibalba", 1),
            ("Spirito dell'Esercito Dorato", 1), ("Promessa dell'oltretomba", 1), ("Sacrificio della Fertilità", 1),
        ],
    },
    "xibalba_b3_xibalba": {
        "religion": "Ombre Maya",
        "name": "B3 - Trono di Xibalba",
        "cards": [
            ("Anima Errante", 3), ("Ix Chel", 3), ("Spirito dei Sepolti", 3), ("Sussurro degli Antenati", 3),
            ("Cenote Sacro", 3), ("Eco dei Morti", 3), ("Fiume dei Morti", 3), ("Tikal", 3), ("Ritorno Infame", 3),
            ("Concentrazione", 3), ("Cura Totale", 2), ("Calice Insanguinato", 3), ("Rituale dei Guardiani", 1),
            ("Rituale Sepolcrale", 1), ("Resurrezione del Sacerdote", 1), ("Maledizione di Xibalba", 1),
            ("Xibalba", 1), ("Vucub.Came", 1), ("Hun-Came", 1), ("Camazotz", 1), ("Ah Puch", 1),
            ("Promessa dell'oltretomba", 1),
        ],
    },

    # Ph-Dak'Gaph - Set B
    "phdk_b1_volere": {
        "religion": "Ph-DakGaph",
        "name": "B1 - Volere del Vuoto",
        "cards": [
            ("Fujn-dar", 3), ("Kah-ok", 3), ("Pkad-nok", 3), ("Ya-ner", 3), ("Sacerdote del Vuoto", 3),
            ("Gub-ner Antico", 3), ("Pkad-nok'ljep", 3), ("Proibizione di Ph", 3), ("Dono di Kah", 3),
            ("Frammento dello Specchio", 3), ("Avidità di Av", 3), ("Rito della Ri-Manifestazione", 3),
            ("Volere di Ph", 1), ("Av'drna", 2), ("Libro di Ya-ner", 2), ("Paradosso di Ykknodar", 1),
            ("Distorsione del Reliquiario", 1), ("Fujn'lyat", 1), ("Gggnag'ljep", 1),
        ],
    },
    "phdk_b2_risveglio": {
        "religion": "Ph-DakGaph",
        "name": "B2 - Presagio del Risveglio",
        "cards": [
            ("Fujn-dar", 3), ("Kah-ok", 3), ("Pkad-nok", 3), ("Ya-ner", 3), ("Sacerdote del Vuoto", 3),
            ("Gub-ner Antico", 3), ("Proibizione di Ph", 3), ("Dono di Kah", 3), ("Frammento dello Specchio", 3),
            ("Avidità di Av", 3), ("Rito della Ri-Manifestazione", 2), ("Distorsione del Reliquiario", 2),
            ("Ph'drna", 1), ("Llakhnal", 2), ("Gggnag'ljep", 1), ("Libro di Ya-ner", 1), ("Ph'kdam", 1),
            ("Paradosso di Ykknodar", 1), ("Maledizione di Ykknodar", 1), ("Risveglio di Ph-Dak'Gaph", 1),
            ("Furia di Llakhnal", 2),
        ],
    },
    "phdk_b3_specchio": {
        "religion": "Ph-DakGaph",
        "name": "B3 - Specchio di Ykknodar",
        "cards": [
            ("Fujn-dar", 3), ("Kah-ok", 3), ("Pkad-nok", 3), ("Ya-ner", 3), ("Sacerdote del Vuoto", 3),
            ("Gub-ner Antico", 3), ("Proibizione di Ph", 3), ("Pkad-nok'ljep", 3), ("Dono di Kah", 3),
            ("Frammento dello Specchio", 3), ("Avidità di Av", 3), ("Volere di Ph", 1), ("Rito della Ri-Manifestazione", 2),
            ("Distorsione del Reliquiario", 2), ("Libro di Ya-ner", 1), ("Paradosso di Ykknodar", 1),
            ("Specchio di Ykknodar", 1), ("Ykknodar", 1), ("Maledizione di Ykknodar", 1), ("Furia di Llakhnal", 1),
            ("Gggnag'ljep", 1),
        ],
    },

    # Mitologia Norrena - Set B
    "norrena_b1_thor": {
        "religion": "Mitologia Norrena",
        "name": "B1 - Concilio di Thor",
        "cards": [
            ("Tanngnjostr", 3), ("Tanngrisnir", 3), ("Huginn", 3), ("Muninn", 3), ("Sif", 3), ("Jordh", 3),
            ("Skadi", 3), ("Thor", 1), ("Figli di Odino", 3), ("Gungnir", 3), ("Járngreipr", 3), ("Megingjörð", 3),
            ("Saga degli Eroi Caduti", 3), ("Tempesta di Asgard", 3), ("Valhalla", 1), ("Yggdrasil", 1),
            ("Mjolnir", 1), ("Loki", 2),
        ],
    },
    "norrena_b2_odino": {
        "religion": "Mitologia Norrena",
        "name": "B2 - Arsenale di Odino",
        "cards": [
            ("Huginn", 3), ("Muninn", 3), ("Tanngnjostr", 3), ("Tanngrisnir", 3), ("Sif", 3), ("Jordh", 3),
            ("Skadi", 3), ("Odino", 1), ("Figli di Odino", 3), ("Gungnir", 3), ("Járngreipr", 3), ("Megingjörð", 2),
            ("Saga degli Eroi Caduti", 3), ("Tempesta di Asgard", 3), ("Valhalla", 1), ("Yggdrasil", 1),
            ("Fenrir", 1), ("Jormungandr", 1), ("Bifrost", 1), ("Loki", 1),
        ],
    },
    "norrena_b3_ragnarok": {
        "religion": "Mitologia Norrena",
        "name": "B3 - Presagi di Ragnarok",
        "cards": [
            ("Tanngnjostr", 3), ("Tanngrisnir", 3), ("Huginn", 3), ("Muninn", 3), ("Sif", 3), ("Jordh", 3),
            ("Loki", 3), ("Skadi", 3), ("Figli di Odino", 3), ("Saga degli Eroi Caduti", 3), ("Valhalla", 1),
            ("Yggdrasil", 1), ("Fenrir", 1), ("Jormungandr", 1), ("Assalto Invernale", 1), ("Ragnarok", 1),
            ("Bifrost", 3), ("Tempesta di Asgard", 3), ("Gungnir", 1), ("Járngreipr", 1), ("Megingjörð", 1),
        ],
    },
}

# Carte neutre "consigliate" per riempire a 45 quando un premade e' corto.
NEUTRAL_FILL_ORDER = [
    ("Barriera Magica", 3),
    ("Concentrazione", 3),
    ("Meditazione", 2),
    ("Cura", 3),
    ("Cura Rapida", 3),
    ("Seguace", 3),
    ("Moribondo", 3),
    ("Ricerca Archeologica", 2),
    ("Rinforzi", 2),
]

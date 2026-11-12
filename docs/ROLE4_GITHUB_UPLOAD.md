# Caricare il contributo Role 4

Questo pacchetto contiene solo i file nuovi o aggiornati del tuo contributo. Non contiene il dataset o una copia completa del repository.

## Passaggi su GitHub

1. Apri la pagina principale di `LoukasIatrou/ML-project`.
2. Dal selettore del branch crea **feature/role4-evaluation**, partendo da `main`. Il gruppo richiede di lavorare su un branch.
3. Estrai `role4_repository_changes.zip` sul computer.
4. Nella pagina principale del nuovo branch scegli **Add file > Upload files**. Carica i file e le cartelle estratti mantenendo i percorsi. Non caricare lo ZIP come unico file e non mettere tutto dentro `tests`.
5. La radice deve ricevere `README.md` e `requirements-evaluation.txt`; le cartelle `src`, `tests`, `docs` e `.github` contengono gli altri file. Su Mac, se `.github` non si vede, usa **Cmd + Shift + .** per mostrare le cartelle nascoste.
6. Usa il messaggio di commit **Add shared evaluation for the Elliptic split**.
7. Apri una pull request dal branch verso `main`. Collega l'issue del task e richiedi la revisione di un compagno, come indicato in `CONTRIBUTING.md`.
8. Controlla che il workflow **Role 4 evaluation tests** passi. Lascia il merge al revisore o al team leader secondo le regole del gruppo.

Il pacchetto è basato sullo ZIP che hai fornito. Il README mantiene il contenuto di quella copia e aggiunge solo la sezione sulla valutazione. Controlla il confronto della pull request per verificare che eventuali aggiornamenti successivi del gruppo rimangano presenti.

## Dove va il codice

| Percorso | Contenuto |
|---|---|
| `src/role4_evaluation.py` | Programma che calcola i punteggi e legge il file condiviso di Role 1. |
| `tests/test_role4_evaluation.py` e `tests/test_role4_split.py` | Controlli automatici. |
| `tests/fixtures/role4/` | Piccoli esempi inventati per provare il programma. |
| `docs/ROLE4_EVALUATION.md` | Guida semplice per i compagni e regole di valutazione. |
| `docs/ROLE4_VALIDATION.md` | Verifiche già eseguite. |

Il file già presente `tests/elliptic_split.csv` resta dov'è e non viene modificato. Non viene incluso di nuovo in questo pacchetto.

## Titolo della pull request

Add shared evaluation for the Elliptic time split

## Descrizione della pull request

The project now has a shared evaluator for baseline and graph models. It reads the existing `tests/elliptic_split.csv`, preserves the 1-34 / 35-49 time split, excludes unknown labels and matches predictions by transaction ID.

The change adds numerical and interface tests, a simulated example, typed functions, strict CSV validation, staged exports, usage instructions and a GitHub Actions workflow. The original shared data is unchanged. The README gains a link to the evaluation guide.

Validation: 51 automated tests passed locally, including 60 numerical reference cases and failed-export regression checks. An integration check used the supplied split file and confirmed 16,670 known-label test transactions, including 1,083 illicit transactions. Prediction scores in that check were invented and do not represent model performance. The first hosted CI run and real-model comparisons are pending.

## Controlli prima della revisione

- Collega l'issue reale del task, se non è già collegata.
- Richiedi un revisore.
- Conferma con il gruppo le scelte ancora proposte: validazione, soglia degli alert, seed e informazioni del grafo consentite.

# Role 4 Guida completa al lavoro svolto

**Che cosa abbiamo costruito e come usarlo**

BSFS x BSML - Graph ML for Money Laundering

> **Aggiornamento, 16 novembre 2026.** Ora ci sono risultati reali. Tutte le 30 esecuzioni dei modelli (Ruoli 2 e 3, 5 seed ciascuno) sono state valutate con questo programma sullo stesso insieme di test. Sono poi state combinate con `src/role4_compare.py`. Le spiegazioni SHAP e GNNExplainer sono in `notebooks/role4_explainability.ipynb`. Risultati e interpretazione AML (in inglese): [RESULTS_AND_INTERPRETATION.md](RESULTS_AND_INTERPRETATION.md). Il testo qui sotto descrive la consegna iniziale.

**Abbiamo costruito un sistema comune per controllare le previsioni dei modelli del gruppo. Il programma e le istruzioni sono pronti per la revisione del team. Abbiamo verificato che il software funzioni; al momento della consegna iniziale non avevamo ancora risultati di modelli realmente addestrati.**

## 1 La domanda del progetto

Il gruppo vuole capire se il machine learning riesce a riconoscere transazioni Bitcoin etichettate come illecite e se le connessioni tra transazioni migliorano i risultati. Un modello impara schemi dai dati e produce una previsione. I modelli su grafo usano anche le relazioni tra transazioni.

## 2 Dove si inserisce il tuo ruolo

| Ruolo | Compito |
| --- | --- |
| Role 1 | Prepara i dati, le risposte conosciute e la divisione tra sviluppo e test. |
| Role 2 | Costruisce modelli tradizionali e valuta se aggiungere informazioni del grafo aiuta. |
| Role 3 | Costruisce e addestra le reti neurali su grafo, seguendo lo stesso split temporale. |
| Il tuo Role 4 | Prepara le regole e il programma di valutazione; dopo confronta i risultati, spiega le previsioni e coordina il report. |

Pensa a un correttore comune: i compagni producono le risposte dei loro modelli, Role 1 fornisce le risposte note e il tuo programma confronta le due cose. Tutti devono usare la stessa griglia di correzione per ottenere un confronto corretto.

## 3 Il prodotto che consegni adesso

La consegna preliminare comprende codice riutilizzabile, regole documentate, un esempio inventato eseguibile, test automatici e istruzioni per GitHub. Permette a Roles 2 e 3 di verificare i propri modelli con lo stesso metodo appena avranno prodotto le previsioni.

Il prodotto attuale valuta i modelli. L’addestramento dei modelli è il lavoro dei compagni; le spiegazioni SHAP/GNN e il report finale saranno la fase successiva del tuo ruolo.

## 4 Quali dati abbiamo effettivamente controllato

Nel repository ricevuto è già presente tests/elliptic_split.csv. Ha una riga per transazione e quattro colonne: txId, time_step, class e split. Abbiamo adattato il programma a questo file senza modificarlo.

| Parte | Totale | Illecite note | Lecite note | Sconosciute |
| --- | --- | --- | --- | --- |
| Train 1-34 | 136.265 | 3.462 | 26.432 | 106.371 |
| Test 35-49 | 67.504 | 1.083 | 15.587 | 50.834 |

Per misurare gli errori servono risposte conosciute: nel test sono disponibili 16.670 transazioni etichettate, cioè 1.083 illecite e 15.587 lecite. Le 50.834 con classe sconosciuta restano fuori dai punteggi. Unknown non significa lecito.

## 5 Che cosa significano le colonne

| Campo | Significato |
| --- | --- |
| txId / transaction_id | Il codice univoco della transazione. Si tratta come testo per preservarlo, non come un numero da usare nei calcoli. |
| time_step | Il periodo della transazione. Il test finale comprende i periodi dal 35 al 49. |
| class / y_true | La risposta conosciuta. Nel file del team class è illicit, licit oppure unknown. Il valutatore usa y_true=1 per illecito e y_true=0 per lecito. |
| split | Indica se la riga appartiene al train o al test. |
| score_illicit | Il punteggio prodotto da un modello: una probabilità stimata tra 0 e 1 di appartenere alla classe illecita. |

Il file originale Elliptic usa anche i codici 1=illecito e 2=lecito. L’adattatore accetta quei codici o le parole usate dal team e li converte esplicitamente. Non trasforma una classe sconosciuta in 0.

## 6 Regole fisse e scelte ancora proposte

La divisione 1-34 per lo sviluppo e 35-49 per il test è già implementata da Role 1. Il programma verifica che il file la rispetti. Il test finale non deve servire a scegliere il modello o la soglia.

Sono ancora proposte da concordare: usare 1-29 per addestrare e 30-34 per validare, una soglia di 0,50 e i seed 0, 1 e 2. La validazione sarebbe interna alla parte chiamata train nel file condiviso. Le informazioni del grafo consentite devono essere documentate per tutti i modelli.

## 7 Come trasformiamo un punteggio in una previsione

Una soglia, o threshold, è il limite oltre il quale segnaliamo una transazione. Nell’esempio usiamo 0,50: un punteggio di 0,80 produce una previsione illecita, mentre 0,30 produce una previsione lecita. Il punteggio è una stima del modello; la classe nota serve a capire se ha ragione.

**L’esempio seguente è interamente inventato. È incluso nei file di prova e non rappresenta risultati di modelli reali.**

| ID | Classe nota | Score | Previsione | Esito |
| --- | --- | --- | --- | --- |
| T1 | Illecita | 0,90 | Illecita | TP - rilevata correttamente |
| T2 | Lecita | 0,80 | Illecita | FP - falso allarme |
| T3 | Illecita | 0,40 | Lecita | FN - caso mancato |
| T4 | Lecita | 0,20 | Lecita | TN - riconosciuta correttamente |
| T5 | Lecita | 0,10 | Lecita | TN - riconosciuta correttamente |
| T6 | Illecita | 0,70 | Illecita | TP - rilevata correttamente |
| T7 | Lecita | 0,30 | Lecita | TN - riconosciuta correttamente |
| T8 | Lecita | 0,05 | Lecita | TN - riconosciuta correttamente |

## 8 Che cosa misurano i risultati

| Misura | Domanda a cui risponde |
| --- | --- |
| Precision | Delle transazioni segnalate, quante sono davvero etichettate illecite? Nell’esempio: 2 su 3, cioè 66,7%. |
| Recall | Di tutte le illecite conosciute, quante abbiamo trovato? Nell’esempio: 2 su 3, cioè 66,7%. |
| F1 | Combina precision e recall con una media armonica. Nell’esempio vale 0,6667. Si calcola anche come 2TP / (2TP + FP + FN). |
| Average precision o AP | Riassume la qualità dell’ordinamento dei punteggi attraverso diverse soglie. Usa gli score originali; nell’esempio vale 0,8056. |
| Accuracy | La quota totale di previsioni corrette. Nell’esempio: 6 su 8, cioè 75%. |

AP non è accuracy e non è identica alla PR-AUC calcolata con il metodo dei trapezi. La consegna consente di scegliere le metriche: abbiamo scelto AP e la riportiamo con quel nome.

Perché accuracy non basta: sui 16.670 test etichettati, un ipotetico sistema che dicesse sempre “lecito” avrebbe circa il 93,5% di risposte corrette, ma troverebbe zero transazioni illecite. È un esempio logico basato sulle classi, non un modello addestrato.

## 9 Come funziona il programma

| Passaggio | Che cosa fa |
| --- | --- |
| Preparazione | prepare_test_manifest legge il formato del team, controlla lo split, esclude gli unknown dal test e restituisce ID, periodo e classe nota. |
| Validazione e abbinamento | evaluate_predictions controlla i punteggi e associa ogni previsione al suo ID. Le righe possono essere in ordine diverso. ID mancanti, extra o duplicati bloccano il confronto. |
| Calcolo | Applica la soglia una volta, conta TP/FP/FN/TN e calcola le metriche complessive e per ciascuno dei 15 periodi di test. |
| Esportazione | main collega questi passaggi ai comandi del terminale e salva i risultati. Le stesse funzioni sono importabili in un notebook. |

## 10 Dove si trova il lavoro nel repository

| Percorso | Contenuto |
| --- | --- |
| src/role4_evaluation.py | Il programma di valutazione, con funzioni descritte e tipi di input/output indicati. |
| requirements-evaluation.txt | Le versioni verificate delle librerie principali. |
| tests/test_role4*.py | Tre file di controlli automatici, con 51 metodi di test. |
| tests/fixtures/role4/ | Piccoli dati inventati e risultati attesi per provare il codice. |
| docs/ROLE4_EVALUATION.md | Guida operativa in inglese per gli altri membri. |
| docs/ROLE4_VALIDATION.md | Verifiche, problemi corretti e misura locale dell’efficienza. |
| docs/ROLE4_REQUIREMENTS_CHECK.md | Controllo dei requisiti e distinzione tra lavoro pronto e ancora da svolgere. |
| docs/ROLE4_AML_CONTEXT.md | Introduzione AML, piano delle spiegazioni e traccia del report. |

## 11 I quattro file prodotti da ogni esecuzione

| Output | Che cosa contiene |
| --- | --- |
| overall_metrics.csv | Punteggi complessivi, conteggi delle classi e degli errori. |
| metrics_per_time_step.csv | Gli stessi risultati per ogni periodo, con il numero di esempi. |
| evaluated_predictions.csv | Ogni transazione con classe nota, score, previsione ed esito TP/FP/FN/TN. |
| run_metadata.json | Modello, seed, soglia, versioni e impronte dei file utilizzati. |

L’impronta manifest_sha256 aiuta a verificare che due modelli siano stati valutati sugli stessi ID, periodi e risposte note. Non certifica come i modelli sono stati addestrati. L’API del notebook restituisce le tabelle in memoria; il comando del terminale salva anche i file.

## 12 Come abbiamo controllato la qualità

Un test automatico sottopone il programma a un caso con risultato atteso e controlla che risponda correttamente. Il controllo finale è stato eseguito ricostruendo una copia del repository originale e applicando lo ZIP, come farà chi riceve il contributo.

| Controllo | Esito verificato |
| --- | --- |
| Test automatici | 51 metodi superati nella copia ricostruita del repository. |
| Riferimento numerico | 60 casi confrontati con scikit-learn: diverse dimensioni, classi sbilanciate, score uguali e soglie estreme. |
| Dati reali di Role 1 | Riconosciute 16.670 righe di test etichettate, con 1.083 illecite e 15.587 lecite. |
| Prova completa | Lettura del file condiviso, previsioni simulate, associazione per ID ed esportazione dei quattro file. |
| Casi particolari | Periodi vuoti, una sola classe, zero alert, valori mancanti e impostazioni non valide. |
| Integrità del pacchetto | ZIP valido, file originali preservati, istruzioni interne collegate correttamente e sintassi del workflow controllata. |

## 13 Problemi trovati e corretti

Un CSV con campi in eccesso poteva essere interpretato con colonne spostate: ora viene rifiutato. Un errore durante l’esportazione poteva lasciare risultati incompleti: ora il programma prepara tutti i file in una posizione temporanea e gestisce gli errori di pubblicazione, preservando le cartelle già esistenti.

Abbiamo inoltre aggiunto controlli espliciti sui tipi dei valori, preservato gli ID testuali e gli zeri iniziali e uniformato i risultati del terminale e del notebook. Se una metrica non è interpretabile, i campi *_defined lo segnalano; i periodi senza dati mantengono punteggi mancanti.

## 14 Perché il codice è più efficiente

Le classificazioni sono calcolate una sola volta, i conteggi derivano da un unico passaggio e le righe sono raggruppate per periodo una sola volta. Le impronte dei file sono calcolate senza caricare tutti i byte contemporaneamente in memoria.

Nella misura locale su 16.670 transazioni, cinque ripetizioni hanno dato una mediana di 0.108 secondi per la versione precedente e 0.045 per quella rivista, circa 2.4 volte più veloce. La misura riguarda il calcolo in memoria, non lettura/salvataggio dei CSV o addestramento. Non è una garanzia di velocità identica su altri computer.

Ambiente verificato: Python 3.12.14, NumPy 2.3.5, pandas 2.2.3 e scikit-learn 1.8.0. Una sessione Colab nuova, l’installazione con download in un ambiente vuoto e l’esecuzione remota di GitHub Actions restano da verificare.

## 15 Come lo useranno Roles 2 e 3

Ogni compagno addestra il proprio modello e produce un CSV con due colonne: txId oppure transaction_id, e score_illicit. Deve usare una sola colonna ID e includere esattamente gli ID di test con classe conosciuta. Se ha predetto tutti i nodi, filtra prima il file usando l’elenco restituito da prepare_test_manifest.

Il modello deve esportare la probabilità della classe illecita. Il compagno deve controllare l’ordine delle classi: non è sempre corretto prendere automaticamente la seconda colonna del suo modello.

## 16 Prima prova senza modelli reali

Apri un terminale nella radice del repository, dove si trovano README.md, src e tests. Installa le librerie:

```bash
python -m pip install -r requirements-evaluation.txt
```

Poi esegui il comando seguente. Le righe con la barra finale continuano lo stesso comando nel terminale Bash di macOS/Linux:

```bash
python -m src.role4_evaluation \
  --truth tests/fixtures/role4/simulated_test_manifest.csv \
  --predictions tests/fixtures/role4/simulated_predictions.csv \
  --model SIMULATED_DEMO --seed 0 --threshold 0.50 \
  --outdir outputs/role4/simulated_demo
```

L’esempio deve dare TP=2, FP=1, FN=1, TN=4, F1=0,6667 e AP=0,8056. Usa una cartella nuova: se quella indicata esiste già, scegli un altro nome.

## 17 Quando arrivano le previsioni vere

Il comando sotto usa il file reale di Role 1. Il percorso del CSV di previsioni è un esempio: va sostituito con il file effettivamente prodotto dal modello.

```bash
python -m src.role4_evaluation \
  --split-file tests/elliptic_split.csv \
  --predictions outputs/role4/rf_seed0_predictions.csv \
  --model RandomForest --seed 0 --threshold 0.50 \
  --outdir outputs/role4/random_forest_seed0
```

| Argomento | Significato |
| --- | --- |
| --split-file | Il file condiviso con ID, periodi, classi e divisione train/test. |
| --predictions | Il CSV delle probabilità prodotte da un modello. |
| --model e --seed | Il nome del modello e il seed realmente utilizzato nell’addestramento. Il seed registra il punto di partenza delle scelte casuali; il valutatore non addestra nulla. |
| --threshold | La soglia concordata prima del test finale. 0,50 è la proposta usata negli esempi. |
| --outdir | Una cartella nuova in cui salvare il risultato di quella esecuzione. |

In Colab si possono importare le due funzioni pubbliche nel notebook dopo aver reso disponibile il repository e impostato la sua radice come cartella di lavoro. La guida inglese contiene l’esempio completo. Per i test automatici: python -m unittest discover -s tests -p "test_role4*.py" -v.

## 18 Cosa è completato e cosa resta

| Parte della consegna | Stato corretto da dichiarare |
| --- | --- |
| Valutazione condivisa | Implementata e verificata localmente, con supporto ai dati del gruppo. |
| F1 e risultati temporali | Implementati. Per il riepilogo precision-recall usiamo AP, con scelta documentata. |
| Contesto AML | Introduzione con fonti e limiti preparata; interpretazione dei risultati da completare dopo i modelli. |
| Spiegazioni delle previsioni | Piano SHAP/PyG preparato. Esecuzione e analisi effettive ancora da svolgere. |
| Relazione e slide | Struttura preparata. Documenti finali ancora da scrivere nei template Word e PowerPoint forniti. |
| GitHub e revisione | File e workflow pronti. Caricamento, esito remoto e approvazione della pull request non verificati da questo ambiente. |

Non abbiamo addestrato modelli di Role 2 o Role 3. Gli score usati nelle prove sono inventati, anche quando sono associati agli ID reali di Role 1. Il superamento dei test dimostra il funzionamento del software nelle verifiche eseguite, non la capacità dei futuri modelli di trovare attività illecite.

## 19 I prossimi passaggi concreti

1. Estrai lo ZIP finale e carica il contenuto nella radice del repository su un branch feature/role4-evaluation, mantenendo le cartelle. Il pacchetto contiene i file da aggiungere o aggiornare, non tutto il progetto e non il dataset.

2. Apri una pull request verso main, collega l’issue del lavoro, controlla GitHub Actions e richiedi un revisore secondo CONTRIBUTING.md. Il README mantiene il testo dello snapshot ricevuto e aggiunge una sezione sulla valutazione.

3. Concorda con il gruppo le scelte ancora proposte e chiedi a Roles 2 e 3 di provare l’interfaccia. Quando arrivano le loro previsioni, esegui lo stesso procedimento per ogni modello e seed.

4. Per completare il ruolo, confronta risultati e periodi, crea i grafici, esegui le spiegazioni e scrivi le conclusioni AML. Per spiegare un modello servono anche il modello addestrato, i dati e il preprocessing; per una GNN serve la corrispondenza tra ID e nodi del grafo.

## 20 Fonti e confini del lavoro

I requisiti vengono da GraphML_roles.pdf e dalle regole del repository ricevuto. Schema e conteggi sono verificati su tests/elliptic_split.csv e confrontati con Final Data Card.html. Le definizioni delle metriche seguono scikit-learn; il contesto iniziale usa UNODC e Weber et al. Le spiegazioni future fanno riferimento a SHAP e PyTorch Geometric.

Riferimenti: scikit-learn.org/stable/modules/model_evaluation.html ; arxiv.org/abs/1908.02591 ; unodc.org/e4j/en/organized-crime/module-4/key-issues/money-laundering.html ; shap.readthedocs.io ; pytorch-geometric.readthedocs.io. Link completi e dettagli sono nelle guide del repository.

**Il risultato di questa fase è uno strumento comune di valutazione pronto per revisione. Il Role 4 completo si conclude con l’analisi dei modelli reali e la consegna dei documenti finali.**

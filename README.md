# NASA EONET API

Questa API scarica gli eventi naturali dalla NASA EONET, li salva in MariaDB e
li rende disponibili tramite semplici endpoint HTTP.

Il database viene aggiornato all'avvio e poi ogni 5 minuti.

## Struttura

```text
api/
  main.py       endpoint HTTP e aggiornamento automatico NASA
  database.py   connessione MariaDB e tutte le query SQL
  schema.sql    struttura delle tabelle
  requirements.txt
compose.yaml    API, MariaDB e phpMyAdmin
```

Non sono presenti repository, service, DTO, factory o altri livelli intermedi.

## Avvio

```bash
docker compose up -d --build
```

- Swagger API: <http://localhost:8000/docs>
- Controllo API: <http://localhost:8000/health>
- phpMyAdmin: <http://localhost:8081>

Le porte sono pubblicate soltanto su `127.0.0.1`, quindi API e phpMyAdmin non
sono raggiungibili direttamente da altri computer della rete.

phpMyAdmin mostra la schermata di login: usare `DB_USER` e `DB_PASSWORD` presenti
nel proprio file `.env`. Le credenziali non vengono inserite automaticamente nel
browser.

## Configurazione

Le credenziali sono lette da `.env` e passate ai container da `compose.yaml`:

```env
DB_NAME=nasa
DB_USER=nasa
DB_PASSWORD=una_password_sicura
DB_ROOT_PASSWORD=una_password_root_sicura
```

Non inserire password direttamente nei file Python.

L'intervallo di aggiornamento è una sola costante in `api/main.py`:

```python
UPDATE_INTERVAL_SECONDS = 5 * 60
```

Dopo una modifica ricostruire l'API con `docker compose up -d --build`.

## Connessione al database

`api/database.py` legge `DB_HOST`, `DB_PORT`, `DB_NAME`, `DB_USER` e
`DB_PASSWORD`, poi apre una connessione PyMySQL.

Tutte le query si trovano nello stesso file e usano parametri `%s`. I valori
ricevuti dal client non vengono concatenati nelle query SQL.

## Endpoint

### Elenco eventi

```text
GET /api/events?status=open&limit=20&offset=0
```

- `status`: `open`, `closed` oppure `all`
- `limit`: da 1 a 500
- `offset`: zero o un numero positivo

### Singolo evento

```text
GET /api/events/EONET_1234
```

Restituisce `404` se l'evento non esiste.

### Stato del servizio

```text
GET /health
```

Mostra la connessione al database, l'intervallo e l'esito dell'ultimo
aggiornamento NASA.

## Come funziona una richiesta

Per `GET /api/events` il flusso è questo:

```text
FastAPI riceve e valida status, limit e offset
→ main.py chiama database.get_events(...)
→ database.py esegue query SQL parametrizzate
→ categorie, fonti e geometrie vengono aggiunte agli eventi
→ FastAPI restituisce JSON
```

Anche `event_id` viene validato: deve contenere da 1 a 100 caratteri, come la
colonna corrispondente nel database.

## Risposte ed errori

Gli endpoint mantengono il formato originale per non rompere eventuali client:

- `/api/events` restituisce una lista JSON;
- `/api/events/{id}` restituisce un oggetto JSON;
- gli errori usano il formato FastAPI `{"detail": "messaggio"}`.

Codici principali:

- `200`: richiesta riuscita;
- `404`: evento inesistente;
- `422`: parametro non valido o mancante;
- `503`: database non disponibile.

Gli errori interni vengono scritti nei log, senza mostrare stack trace o
credenziali al client.

## Autenticazione e JWT

Questa API espone soltanto dati pubblici NASA con richieste `GET`. Non esistono
utenti, password, operazioni di modifica o dati privati, quindi autenticazione e
JWT non sono necessari. Se in futuro verranno aggiunti endpoint `POST`, `PUT` o
`DELETE`, occorrerà introdurre autenticazione e controlli dei permessi prima di
esporli.

## Come aggiungere un endpoint

1. Aggiungere in `database.py` una funzione con una query parametrizzata.
2. Aggiungere in `main.py` una funzione con `@app.get(...)`.
3. Lasciare a FastAPI la validazione dei parametri con `Query` e tipi Python.
4. Restituire il dato oppure un errore `HTTPException` con il codice corretto.

Esempio minimo:

```python
@app.get("/api/example/{event_id}")
def get_example(event_id: str):
    event = database.get_event_by_id(event_id)
    if event is None:
        raise HTTPException(status_code=404, detail="Evento non trovato")
    return event
```

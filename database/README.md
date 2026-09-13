# Database di consegna

Il database utilizzato è MariaDB 11.4. La consegna comprende:

- [../api/schema.sql](../api/schema.sql): schema completo delle sette tabelle;
- [dati.sql](dati.sql): esportazione del 14 settembre 2026 delle sei tabelle di dominio, con struttura e dati presenti nel database locale;
- [diagramma ER](../docs/schema-er.md): entità, attributi e relazioni.

Lo snapshot contiene `events`, `categories`, `sources`, `event_categories`, `event_sources` e `geometries`. Non è l'archivio completo NASA: contiene quanto acquisito dall'applicazione. `sync_runs` è un registro operativo e viene creato vuoto dallo schema; i suoi log non fanno parte dell'esportazione. Non sono inclusi utenti MariaDB o credenziali.

## Avvio normale

Seguire il README principale: l'API crea lo schema e acquisisce i dati dalla NASA. Il volume `db_data` mantiene il database locale, ma non viene caricato su GitHub.

## Ripristino dello snapshot

Usare una copia dedicata del progetto, con `.env` configurato. I comandi seguenti sono per PowerShell. Il dump sostituisce le sei tabelle di dominio: eseguirli soltanto sul database destinato alla riproduzione della consegna.

```powershell
docker compose up -d db
docker compose stop api web
docker compose ps
```

Attendere che `db` sia `healthy`, quindi importare schema e dati. Le credenziali vengono lette dall'ambiente del container, senza inserirle nei file SQL.

```powershell
docker compose cp api/schema.sql db:/tmp/nasa-schema.sql
docker compose cp database/dati.sql db:/tmp/nasa-dati.sql
docker compose exec -T db sh -c 'MYSQL_PWD="$MARIADB_PASSWORD" mariadb --user="$MARIADB_USER" "$MARIADB_DATABASE" < /tmp/nasa-schema.sql'
docker compose exec -T db sh -c 'MYSQL_PWD="$MARIADB_PASSWORD" mariadb --user="$MARIADB_USER" "$MARIADB_DATABASE" < /tmp/nasa-dati.sql'
docker compose exec -T db sh -c 'MYSQL_PWD="$MARIADB_PASSWORD" mariadb --user="$MARIADB_USER" "$MARIADB_DATABASE" -e "SELECT COUNT(*) AS eventi FROM events; SELECT COUNT(*) AS geometrie FROM geometries;"'
```

Per consultare lo snapshot senza sincronizzazioni avviare soltanto phpMyAdmin:

```powershell
docker compose up -d phpmyadmin
```

Aprire <http://localhost:8081> e accedere con le credenziali di `.env`.
Avviando anche l'API con `docker compose up -d --build`, ripartono gli aggiornamenti NASA e lo snapshot può cambiare.

## Aggiornare l'esportazione

Con il database in esecuzione:

```powershell
docker compose exec -T db sh -c 'MYSQL_PWD="$MARIADB_PASSWORD" mariadb-dump --user="$MARIADB_USER" --single-transaction --skip-comments --no-tablespaces --result-file=/tmp/nasa-consegna.sql "$MARIADB_DATABASE" events categories sources event_categories event_sources geometries'
docker compose cp db:/tmp/nasa-consegna.sql database/dati.sql
```

Aggiornare la data indicata sopra e verificare il contenuto prima del commit. L'esportazione usa una transazione coerente per le tabelle InnoDB e il file viene copiato direttamente dal container per conservarne la codifica.

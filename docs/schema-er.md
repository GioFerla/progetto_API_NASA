# Schema del database

Il diagramma documenta lo schema già esistente in [api/schema.sql](../api/schema.sql), senza modificarlo. Il database utilizzato è MariaDB 11.4.

```mermaid
erDiagram
    events ||--o{ event_categories : appartiene
    categories ||--o{ event_categories : classifica
    events ||--o{ event_sources : cita
    sources ||--o{ event_sources : documenta
    events ||--o{ geometries : possiede

    events {
        varchar(100) id PK
        varchar(500) title
        text description
        varchar(1000) link
        datetime closed_at
        timestamp created_at
        timestamp updated_at
    }
    categories {
        varchar(100) id PK
        varchar(255) title
        text description
        varchar(1000) link
        timestamp created_at
        timestamp updated_at
    }
    sources {
        varchar(100) id PK
        varchar(255) title
        varchar(1000) source_url
        varchar(1000) link
        timestamp created_at
        timestamp updated_at
    }
    event_categories {
        varchar(100) event_id PK,FK
        varchar(100) category_id PK,FK
    }
    event_sources {
        varchar(100) event_id PK,FK
        varchar(100) source_id PK,FK
        varchar(1500) reference_url
    }
    geometries {
        bigint_unsigned id PK
        varchar(100) event_id FK
        datetime observed_at
        varchar(30) geometry_type
        longtext coordinates
        decimal(10_7) longitude
        decimal(10_7) latitude
        decimal(10_7) bbox_min_longitude
        decimal(10_7) bbox_min_latitude
        decimal(10_7) bbox_max_longitude
        decimal(10_7) bbox_max_latitude
        decimal(15_5) magnitude_value
        varchar(100) magnitude_unit
        varchar(255) magnitude_description
        timestamp created_at
    }
    sync_runs {
        bigint_unsigned id PK
        varchar(100) api_name
        datetime started_at
        datetime completed_at
        varchar(20) status
        int records_received
        int records_created
        int records_updated
        text error_message
    }
```

`PK` indica la chiave primaria; `FK` la chiave esterna. `||--o{` indica una relazione uno a zero o molti. Le chiavi delle tabelle associative sono composte: eventi e categorie, così come eventi e fonti, hanno relazioni molti a molti. Ogni geometria appartiene a un solo evento. `sync_runs` registra le sincronizzazioni e non ha chiavi esterne verso le altre tabelle.

Nel diagramma `decimal(10_7)` e `decimal(15_5)` rappresentano rispettivamente i tipi SQL `DECIMAL(10,7)` e `DECIMAL(15,5)`. Gli identificativi numerici di geometrie e sincronizzazioni sono auto-incrementali. Tutte le chiavi esterne prevedono `ON DELETE CASCADE` e `ON UPDATE CASCADE`.

`closed_at` nullo identifica un evento aperto. Le coordinate sono conservate come testo JSON con vincolo `JSON_VALID`; longitudine, latitudine e limiti geografici sono valori derivati. Sono presenti indici espliciti su `events.closed_at` e `geometries.event_id`. Nullabilità, valori predefiniti e definizione SQL esatta sono consultabili nello schema sorgente.

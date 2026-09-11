"""Connessione MariaDB e query SQL dell'applicazione."""

import json
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import pymysql
from pymysql.cursors import DictCursor


# Tutti i dati sensibili arrivano dall'ambiente, mai dal codice sorgente.
DB_HOST = os.getenv("DB_HOST", "db")
DB_PORT = int(os.getenv("DB_PORT", "3306"))
DB_NAME = os.getenv("DB_NAME", "nasa")
DB_USER = os.getenv("DB_USER", "nasa")
DB_PASSWORD = os.environ["DB_PASSWORD"]


def open_database_connection():
    return pymysql.connect(
        host=DB_HOST,
        port=DB_PORT,
        database=DB_NAME,
        user=DB_USER,
        password=DB_PASSWORD,
        charset="utf8mb4",
        cursorclass=DictCursor,
        autocommit=False,
    )


def create_tables() -> None:
    """Crea le tabelle al primo avvio. Non modifica quelle già esistenti."""
    schema_file = Path(__file__).with_name("schema.sql")
    sql_statements = schema_file.read_text(encoding="utf-8").split(";")

    connection = open_database_connection()
    try:
        with connection.cursor() as cursor:
            for sql_statement in sql_statements:
                if sql_statement.strip():
                    cursor.execute(sql_statement)
        connection.commit()
    except Exception:
        connection.rollback()
        raise
    finally:
        connection.close()


def parse_nasa_date(date_text: str | None):
    if not date_text:
        return None

    parsed_date = datetime.fromisoformat(date_text.replace("Z", "+00:00"))
    if parsed_date.tzinfo is not None:
        parsed_date = parsed_date.astimezone(timezone.utc).replace(tzinfo=None)
    return parsed_date


def get_coordinate_values(coordinates: Any):
    """Estrae tutte le coppie longitudine/latitudine da Point e Polygon."""
    if (
        isinstance(coordinates, list)
        and len(coordinates) >= 2
        and isinstance(coordinates[0], (int, float))
        and isinstance(coordinates[1], (int, float))
    ):
        yield float(coordinates[0]), float(coordinates[1])
        return

    if isinstance(coordinates, list):
        for child in coordinates:
            yield from get_coordinate_values(child)


def start_sync() -> int:
    connection = open_database_connection()
    try:
        with connection.cursor() as cursor:
            cursor.execute(
                """
                INSERT INTO sync_runs (api_name, started_at, status)
                VALUES (%s, UTC_TIMESTAMP(), %s)
                """,
                ("NASA_EONET", "RUNNING"),
            )
            sync_id = cursor.lastrowid
        connection.commit()
        return sync_id
    except Exception:
        connection.rollback()
        raise
    finally:
        connection.close()


def mark_sync_as_failed(sync_id: int, error_message: str) -> None:
    connection = open_database_connection()
    try:
        with connection.cursor() as cursor:
            cursor.execute(
                """
                UPDATE sync_runs
                SET status = %s, completed_at = UTC_TIMESTAMP(), error_message = %s
                WHERE id = %s
                """,
                ("FAILED", error_message[:4000], sync_id),
            )
        connection.commit()
    except Exception:
        connection.rollback()
        raise
    finally:
        connection.close()


def save_event(cursor, nasa_event: dict) -> bool:
    """Inserisce o aggiorna un evento. Restituisce True se l'evento è nuovo."""
    event_id = nasa_event["id"]

    cursor.execute("SELECT 1 FROM events WHERE id = %s", (event_id,))
    event_is_new = cursor.fetchone() is None

    cursor.execute(
        """
        INSERT INTO events (id, title, description, link, closed_at, updated_at)
        VALUES (%s, %s, %s, %s, %s, UTC_TIMESTAMP())
        ON DUPLICATE KEY UPDATE
            title = VALUES(title),
            description = VALUES(description),
            link = VALUES(link),
            closed_at = VALUES(closed_at),
            updated_at = UTC_TIMESTAMP()
        """,
        (
            event_id,
            nasa_event.get("title") or event_id,
            nasa_event.get("description"),
            nasa_event.get("link"),
            parse_nasa_date(nasa_event.get("closed")),
        ),
    )
    return event_is_new


def replace_event_categories(cursor, event_id: str, nasa_categories: list) -> None:
    cursor.execute("DELETE FROM event_categories WHERE event_id = %s", (event_id,))

    for nasa_category in nasa_categories:
        category_id = nasa_category.get("id")
        if not category_id:
            continue

        cursor.execute(
            """
            INSERT INTO categories (id, title)
            VALUES (%s, %s)
            ON DUPLICATE KEY UPDATE title = VALUES(title)
            """,
            (category_id, nasa_category.get("title") or category_id),
        )
        cursor.execute(
            """
            INSERT IGNORE INTO event_categories (event_id, category_id)
            VALUES (%s, %s)
            """,
            (event_id, category_id),
        )


def replace_event_sources(cursor, event_id: str, nasa_sources: list) -> None:
    cursor.execute("DELETE FROM event_sources WHERE event_id = %s", (event_id,))

    for nasa_source in nasa_sources:
        source_id = nasa_source.get("id")
        if not source_id:
            continue

        cursor.execute("INSERT IGNORE INTO sources (id) VALUES (%s)", (source_id,))
        cursor.execute(
            """
            INSERT INTO event_sources (event_id, source_id, reference_url)
            VALUES (%s, %s, %s)
            """,
            (event_id, source_id, nasa_source.get("url")),
        )


def replace_event_geometries(cursor, event_id: str, nasa_geometries: list) -> None:
    cursor.execute("DELETE FROM geometries WHERE event_id = %s", (event_id,))

    for nasa_geometry in nasa_geometries:
        observed_at = parse_nasa_date(nasa_geometry.get("date"))
        coordinates = nasa_geometry.get("coordinates")
        if observed_at is None or not isinstance(coordinates, list):
            continue

        coordinate_values = list(get_coordinate_values(coordinates))
        longitudes = [value[0] for value in coordinate_values]
        latitudes = [value[1] for value in coordinate_values]
        is_point = nasa_geometry.get("type") == "Point" and coordinate_values

        cursor.execute(
            """
            INSERT INTO geometries (
                event_id, observed_at, geometry_type, coordinates,
                longitude, latitude,
                bbox_min_longitude, bbox_min_latitude,
                bbox_max_longitude, bbox_max_latitude,
                magnitude_value, magnitude_unit, magnitude_description
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """,
            (
                event_id,
                observed_at,
                nasa_geometry.get("type") or "Unknown",
                json.dumps(coordinates),
                coordinate_values[0][0] if is_point else None,
                coordinate_values[0][1] if is_point else None,
                min(longitudes) if longitudes else None,
                min(latitudes) if latitudes else None,
                max(longitudes) if longitudes else None,
                max(latitudes) if latitudes else None,
                nasa_geometry.get("magnitudeValue"),
                nasa_geometry.get("magnitudeUnit"),
                nasa_geometry.get("magnitudeDescription"),
            ),
        )


def save_nasa_events(nasa_events: list[dict], sync_id: int) -> None:
    """Salva un aggiornamento NASA completo in una singola transazione."""
    created_events = 0
    updated_events = 0

    connection = open_database_connection()
    try:
        with connection.cursor() as cursor:
            for nasa_event in nasa_events:
                event_id = nasa_event.get("id")
                if not event_id:
                    continue

                if save_event(cursor, nasa_event):
                    created_events += 1
                else:
                    updated_events += 1

                # La risposta NASA è completa: le relazioni possono essere riscritte.
                replace_event_categories(
                    cursor, event_id, nasa_event.get("categories") or []
                )
                replace_event_sources(
                    cursor, event_id, nasa_event.get("sources") or []
                )
                replace_event_geometries(
                    cursor, event_id, nasa_event.get("geometry") or []
                )

            cursor.execute(
                """
                UPDATE sync_runs
                SET status = %s,
                    completed_at = UTC_TIMESTAMP(),
                    records_received = %s,
                    records_created = %s,
                    records_updated = %s,
                    error_message = NULL
                WHERE id = %s
                """,
                ("SUCCESS", len(nasa_events), created_events, updated_events, sync_id),
            )

        connection.commit()
    except Exception:
        connection.rollback()
        raise
    finally:
        connection.close()


def get_last_sync():
    connection = open_database_connection()
    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
            cursor.execute(
                """
                SELECT status, started_at, completed_at,
                       records_received, records_created, records_updated,
                       error_message
                FROM sync_runs
                ORDER BY id DESC
                LIMIT 1
                """
            )
            last_sync = cursor.fetchone()
    finally:
        connection.close()

    if last_sync is None:
        return None

    return {
        "status": last_sync["status"].lower(),
        "started_at": last_sync["started_at"],
        "completed_at": last_sync["completed_at"],
        "records_received": last_sync["records_received"],
        "records_created": last_sync["records_created"],
        "records_updated": last_sync["records_updated"],
        "error": last_sync["error_message"],
    }


def add_details_to_event(connection, event: dict) -> dict:
    """Aggiunge categorie, fonti e geometrie a un evento letto dal database."""
    event_id = event["id"]

    with connection.cursor() as cursor:
        cursor.execute(
            """
            SELECT categories.id, categories.title
            FROM categories
            JOIN event_categories ON event_categories.category_id = categories.id
            WHERE event_categories.event_id = %s
            ORDER BY categories.title
            """,
            (event_id,),
        )
        event["categories"] = cursor.fetchall()

        cursor.execute(
            """
            SELECT source_id AS id, reference_url AS url
            FROM event_sources
            WHERE event_id = %s
            ORDER BY source_id
            """,
            (event_id,),
        )
        event["sources"] = cursor.fetchall()

        cursor.execute(
            """
            SELECT observed_at AS date,
                   geometry_type AS type,
                   coordinates,
                   magnitude_value AS magnitudeValue,
                   magnitude_unit AS magnitudeUnit,
                   magnitude_description AS magnitudeDescription
            FROM geometries
            WHERE event_id = %s
            ORDER BY observed_at
            """,
            (event_id,),
        )
        event["geometry"] = cursor.fetchall()

    for geometry in event["geometry"]:
        geometry["coordinates"] = json.loads(geometry["coordinates"])
        if geometry["magnitudeValue"] is not None:
            # Mantiene lo stesso tipo JSON restituito dalla versione precedente.
            geometry["magnitudeValue"] = str(geometry["magnitudeValue"])

    event["status"] = "closed" if event["closed"] else "open"
    return event


def get_events(status: str, limit: int, offset: int) -> list[dict]:
    # Il frammento WHERE non contiene input libero: deriva da tre valori già validati.
    where_clause = ""
    if status == "open":
        where_clause = "WHERE events.closed_at IS NULL"
    elif status == "closed":
        where_clause = "WHERE events.closed_at IS NOT NULL"

    connection = open_database_connection()
    try:
        with connection.cursor() as cursor:
            cursor.execute(
                f"""
                SELECT events.id, events.title, events.description, events.link,
                       events.closed_at AS closed,
                       MAX(geometries.observed_at) AS last_geometry_date,
                       events.updated_at
                FROM events
                LEFT JOIN geometries ON geometries.event_id = events.id
                {where_clause}
                GROUP BY events.id, events.title, events.description, events.link,
                         events.closed_at, events.updated_at
                ORDER BY last_geometry_date DESC, events.updated_at DESC
                LIMIT %s OFFSET %s
                """,
                (limit, offset),
            )
            events = cursor.fetchall()

        for event in events:
            add_details_to_event(connection, event)
        return events
    finally:
        connection.close()


def get_event_by_id(event_id: str):
    connection = open_database_connection()
    try:
        with connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT events.id, events.title, events.description, events.link,
                       events.closed_at AS closed,
                       MAX(geometries.observed_at) AS last_geometry_date,
                       events.updated_at
                FROM events
                LEFT JOIN geometries ON geometries.event_id = events.id
                WHERE events.id = %s
                GROUP BY events.id, events.title, events.description, events.link,
                         events.closed_at, events.updated_at
                """,
                (event_id,),
            )
            event = cursor.fetchone()

        if event is None:
            return None
        return add_details_to_event(connection, event)
    finally:
        connection.close()

import asyncio
import logging
from contextlib import asynccontextmanager, suppress
from typing import Literal

import httpx
import pymysql
from fastapi import FastAPI, HTTPException, Path, Query

from api import database


# Per cambiare la frequenza basta modificare questo valore.
UPDATE_INTERVAL_SECONDS = 5 * 60

NASA_EVENTS_URL = "https://eonet.gsfc.nasa.gov/api/v3/events"
NASA_EVENTS_LIMIT = 500

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def update_database_from_nasa() -> None:
    """Scarica gli eventi NASA e li salva nel database."""
    sync_id = None

    try:
        sync_id = database.start_sync()

        response = httpx.get(
            NASA_EVENTS_URL,
            params={"status": "all", "limit": NASA_EVENTS_LIMIT},
            timeout=30,
            follow_redirects=True,
        )
        response.raise_for_status()

        response_body = response.json()
        nasa_events = response_body.get("events")
        if not isinstance(nasa_events, list):
            raise ValueError("La risposta NASA non contiene una lista di eventi")

        database.save_nasa_events(nasa_events, sync_id)
        logger.info("Aggiornamento completato: %s eventi ricevuti", len(nasa_events))

    except Exception as error:
        logger.exception("Aggiornamento NASA non riuscito")
        if sync_id is not None:
            try:
                database.mark_sync_as_failed(sync_id, str(error))
            except Exception:
                logger.exception("Impossibile salvare l'errore nel database")


async def update_database_every_five_minutes() -> None:
    """Aggiorna subito il database e poi ripete il lavoro ogni 5 minuti."""
    while True:
        cycle_start = asyncio.get_running_loop().time()
        await asyncio.to_thread(update_database_from_nasa)

        elapsed_seconds = asyncio.get_running_loop().time() - cycle_start
        seconds_until_next_update = max(0, UPDATE_INTERVAL_SECONDS - elapsed_seconds)
        await asyncio.sleep(seconds_until_next_update)


@asynccontextmanager
async def application_lifespan(app: FastAPI):
    database.create_tables()
    update_task = asyncio.create_task(update_database_every_five_minutes())

    try:
        yield
    finally:
        update_task.cancel()
        with suppress(asyncio.CancelledError):
            await update_task


app = FastAPI(
    title="NASA EONET API",
    description="Eventi naturali NASA salvati in MariaDB.",
    version="1.0.0",
    lifespan=application_lifespan,
)


@app.get("/", tags=["system"])
def get_api_information():
    return {"service": "NASA EONET API", "documentation": "/docs"}


@app.get("/health", tags=["system"])
def get_health():
    try:
        last_update = database.get_last_sync()
    except pymysql.MySQLError:
        logger.exception("Controllo del database non riuscito")
        raise HTTPException(status_code=503, detail="Database non disponibile")

    return {
        "status": "ok",
        "database": "connected",
        "update_interval_seconds": UPDATE_INTERVAL_SECONDS,
        "last_update": last_update,
    }


@app.get("/api/events", tags=["events"])
def get_events(
    status: Literal["open", "closed", "all"] = Query(default="all"),
    limit: int = Query(default=100, ge=1, le=500),
    offset: int = Query(default=0, ge=0),
):
    try:
        return database.get_events(status, limit, offset)
    except pymysql.MySQLError:
        logger.exception("Lettura degli eventi non riuscita")
        raise HTTPException(status_code=503, detail="Database non disponibile")


@app.get("/api/events/{event_id}", tags=["events"])
def get_event(event_id: str = Path(min_length=1, max_length=100)):
    try:
        event = database.get_event_by_id(event_id)
    except pymysql.MySQLError:
        logger.exception("Lettura dell'evento non riuscita")
        raise HTTPException(status_code=503, detail="Database non disponibile")

    if event is None:
        raise HTTPException(status_code=404, detail="Evento non trovato")

    return event

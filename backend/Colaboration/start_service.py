import os
import time
import psycopg
from psycopg import OperationalError
import uvicorn

HOST = os.getenv("POSTGRES_HOST")
PORT = os.getenv("POSTGRES_PORT", "5432")
USER = os.getenv("AUTH_USERNAME")
PASSWORD = os.getenv("AUTH_PASSWORD")
DATABASE = os.getenv("POSTGRES_DB")
CONNECTOR = os.getenv("DB_CONNECTOR", "sqlite").lower()


def wait_for_db():
    if CONNECTOR not in {"postgres", "postgresql"}:
        return

    while True:
        try:
            with psycopg.connect(
                host=HOST,
                port=int(PORT),
                user=USER,
                password=PASSWORD,
                dbname=DATABASE,
            ):
                break
        except OperationalError:
            print("Waiting for database...")
            time.sleep(1)


if __name__ == "__main__":
    wait_for_db()
    uvicorn.run("src.server:app", host="0.0.0.0", port=6704)
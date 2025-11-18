import os
import time
import psycopg
from psycopg import OperationalError
import uvicorn

HOST = os.getenv('POSTGRES_HOST')
PORT = int(os.getenv('POSTGRES_PORT'))
USER = os.getenv('AUTH_USERNAME')
PASSWORD = os.getenv('AUTH_PASSWORD')
DATABASE = os.getenv('POSTGRES_DB')


def wait_for_db():
    while True:
        try:
            # psycopg v3
            with psycopg.connect(
                host=HOST,
                port=PORT,
                user=USER,
                password=PASSWORD,
                dbname=DATABASE,
            ) as conn:
                break
        except OperationalError:
            print("Waiting for database...")
            time.sleep(1)


if __name__ == "__main__":
    wait_for_db()
    uvicorn.run("src.server:app", host="0.0.0.0", port=6701)

import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker


class DatabaseConnector:
    """Factory for SQLAlchemy engines.

    The connector type is selected via the ``DB_CONNECTOR`` environment
    variable. Database credentials are read from ``USERNAME`` and ``PASSWORD``
    environment variables for non-SQLite backends.

    Supported connectors:
      - sqlite: uses a SQLite file (path via SQLITE_PATH or default 'database.db').
      - sqlite-local: uses a local SQLite file for development (path via SQLITE_LOCAL_PATH or default 'local.db').
      - mysql (or msql): MySQL via PyMySQL.
      - postgres (or postgresql): PostgreSQL via psycopg.
    """

    def __init__(self):
        self.connector = os.getenv("DB_CONNECTOR", "sqlite").lower()
        self._engine = None

    def get_engine(self):
        if self._engine:
            return self._engine

        user = os.getenv("AUTH_USERNAME")
        password = os.getenv("AUTH_PASSWORD")

        # SQLite file-based
        if self.connector == "sqlite":
            db_path = os.getenv("SQLITE_PATH", "database.db")
            url = f"sqlite:///{db_path}"

        # Local SQLite for development
        elif self.connector == "sqlite-local":
            db_path = os.getenv("SQLITE_LOCAL_PATH", "local.db")
            url = f"sqlite:///{db_path}"

        # MySQL / MariaDB
        elif self.connector in {"mysql", "msql"}:
            host = os.getenv("MYSQL_HOST")
            port = os.getenv("MYSQL_PORT")
            db = os.getenv("MYSQL_DB", "database")
            url = f"mysql+pymysql://{user}:{password}@{host}:{port}/{db}"

        # PostgreSQL
        elif self.connector in {"postgres", "postgresql"}:
            host = os.getenv("POSTGRES_HOST")
            port = os.getenv("POSTGRES_PORT")
            db = os.getenv("POSTGRES_DB", "database")
            url = f"postgresql+psycopg://{user}:{password}@{host}:{port}/{db}"

        else:
            raise ValueError(f"Unsupported DB_CONNECTOR: {self.connector}")

        # create engine with pool_pre_ping to handle stale connections
        self._engine = create_engine(url, pool_pre_ping=True)
        return self._engine

    def get_session(self):
        engine = self.get_engine()
        return sessionmaker(autocommit=False, autoflush=False, bind=engine)()


# Instantiate connector and expose session factory
db_connector = DatabaseConnector()
engine = db_connector.get_engine()
AUTH_SESSION = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def get_db():
    db = AUTH_SESSION()
    try:
        yield db
    finally:
        db.close()

"""Database connection and session management for Azure SQL."""

import urllib.parse
from collections.abc import Generator
from contextlib import contextmanager

from sqlalchemy import create_engine
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session, sessionmaker

from models import Base


def create_azure_sql_engine(
    *,
    server: str,
    database: str,
    username: str,
    password: str,
    port: int = 1433,
    driver: str = "ODBC Driver 18 for SQL Server",
    encrypt: bool = True,
    trust_server_certificate: bool = False,
    connection_timeout: int = 30,
    echo: bool = False,
) -> Engine:
    """Create a SQLAlchemy engine for Azure SQL Database.

    :param server: Azure SQL server address (e.g., 'my-sql.database.windows.net')
    :param database: Database name
    :param username: Database username
    :param password: Database password
    :param port: Server port (default: 1433)
    :param driver: ODBC driver name (default: 'ODBC Driver 18 for SQL Server')
    :param encrypt: Whether to encrypt connection (default: True)
    :param trust_server_certificate: Trust server certificate (default: False)
    :param connection_timeout: Connection timeout in seconds (default: 30)
    :param echo: Whether to log SQL statements (default: False)

    :return: SQLAlchemy Engine instance

    Example:
        >>> engine = create_azure_sql_engine(
        ...     server="my-sql.database.windows.net",
        ...     database="booking-service",
        ...     username="your-username",
        ...     password="your-password",
        ... )

    """
    odbc_params = {
        "Driver": f"{{{driver}}}",
        "Server": f"tcp:{server},{port}",
        "Database": database,
        "Uid": username,
        "Pwd": password,
        "Encrypt": "yes" if encrypt else "no",
        "TrustServerCertificate": "yes" if trust_server_certificate else "no",
        "Connection Timeout": str(connection_timeout),
    }

    odbc_connection_string = ";".join(f"{k}={v}" for k, v in odbc_params.items())
    encoded_connection_string = urllib.parse.quote_plus(odbc_connection_string)
    connection_url = f"mssql+pyodbc:///?odbc_connect={encoded_connection_string}"
    return create_engine(connection_url, echo=echo)


def create_engine_from_connection_string(
    connection_string: str,
    *,
    echo: bool = False,
) -> Engine:
    """Create a SQLAlchemy engine from an ODBC connection string.

    :param connection_string: Full ODBC connection string
    :param echo: Whether to log SQL statements (default: False)

    :return: SQLAlchemy Engine instance

    Example:
        >>> conn_str = "Driver={ODBC Driver 18 for SQL Server};Server=tcp:my-sql.database.windows.net,1433;..."
        >>> engine = create_engine_from_connection_string(conn_str)

    """
    encoded_connection_string = urllib.parse.quote_plus(connection_string)
    connection_url = f"mssql+pyodbc:///?odbc_connect={encoded_connection_string}"

    return create_engine(connection_url, echo=echo)


class DatabaseManager:
    """Manager class for database operations."""

    def __init__(self, engine: Engine) -> None:
        """Initialize the database manager.

        :param engine: SQLAlchemy Engine instance
        """
        self.engine = engine
        self.SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

    def create_tables(self) -> None:
        """Create all database tables."""
        Base.metadata.create_all(bind=self.engine)

    def drop_tables(self) -> None:
        """Drop all database tables."""
        Base.metadata.drop_all(bind=self.engine)

    def get_session(self) -> Session:
        """Get a new database session.

        :return: SQLAlchemy Session instance
        """
        return self.SessionLocal()

    @contextmanager
    def session_scope(self) -> Generator[Session]:
        """Provide a transactional scope around a series of operations.

        :yield: SQLAlchemy Session instance

        Example:
            >>> with db_manager.session_scope() as session:
            ...     user = User(first_name="John", last_name="Doe", email="john@example.com")
            ...     session.add(user)

        """
        session = self.SessionLocal()
        try:
            yield session
            session.commit()
        except Exception:
            session.rollback()
            raise
        finally:
            session.close()

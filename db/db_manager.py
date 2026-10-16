import os
import tempfile

import mysql.connector
from mysql.connector import Error
from dotenv import load_dotenv

load_dotenv()


def get_secret(key, default=None):
    """Get a database setting from environment variables or Streamlit secrets."""
    value = os.getenv(key)

    if value is not None:
        return value

    try:
        import streamlit as st

        if key in st.secrets:
            return st.secrets[key]
    except Exception:
        pass

    return default


def get_db_config():
    """Build the MySQL connection configuration."""
    config = {
        "host": get_secret("DB_HOST"),
        "user": get_secret("DB_USER"),
        "password": get_secret("DB_PASSWORD"),
        "database": get_secret("DB_NAME"),
    }

    port = get_secret("DB_PORT")

    if port:
        config["port"] = int(port)

    ssl_ca = get_secret("DB_SSL_CA")

    if ssl_ca:
        if "BEGIN CERTIFICATE" in ssl_ca:
            certificate_file = tempfile.NamedTemporaryFile(
                mode="w",
                suffix=".pem",
                delete=False,
            )
            certificate_file.write(ssl_ca)
            certificate_file.close()
            config["ssl_ca"] = certificate_file.name
        else:
            config["ssl_ca"] = ssl_ca

    return config


class DatabaseConnection:
    """Singleton class for managing the MySQL database connection."""

    _instance = None
    _connection = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(DatabaseConnection, cls).__new__(cls)
        return cls._instance

    
    
    
    def connect(self):
        """Create or reuse a live MySQL connection."""
        if self._connection is not None:
            try:
                if self._connection.is_connected():
                    # Verify the connection is responsive, not just marked open.
                    self._connection.ping(reconnect=True, attempts=2, delay=1)
                    return self._connection
            except Error:
                try:
                    self._connection.close()
                except Error:
                    pass
                finally:
                    self._connection = None

        try:
            config = get_db_config()
            self._connection = mysql.connector.connect(
                **config,
                connection_timeout=15,
                autocommit=False,
                use_pure=True,
            )
            print("Database connection established successfully.", flush=True)
            return self._connection

        except Exception as exc:
            print(
                "Database connection failed: "
                f"type={type(exc).__name__}, "
                f"errno={getattr(exc, 'errno', None)}, "
                f"sqlstate={getattr(exc, 'sqlstate', None)}",
                flush=True,
            )
            self._connection = None
            return None




    
    def close(self):
        """Close the shared database connection safely."""
        conn = self._connection
        self._connection = None

        if conn is not None:
            try:
                conn.close()
            except Error as exc:
                print(
                    "Database close warning: "
                    f"type={type(exc).__name__}, "
                    f"errno={getattr(exc, 'errno', None)}",
                    flush=True,
                )


    def execute(self, query, params=None):
        """Execute a statement and commit on success."""
        conn = self.connect()

        if conn is None:
            return False

        cursor = None

        try:
            cursor = conn.cursor()

            if params is not None:
                cursor.execute(query, params)
            else:
                cursor.execute(query)

            conn.commit()
            return True

        except Error as e:
            conn.rollback()
            print(f"SQL execution error: {e}")
            return False

        finally:
            if cursor is not None:
                cursor.close()

    def fetch(self, query, params=None):
        """Execute a SELECT query and return all rows."""
        conn = self.connect()

        if conn is None:
            return []

        cursor = None

        try:
            cursor = conn.cursor(dictionary=True)

            if params is not None:
                cursor.execute(query, params)
            else:
                cursor.execute(query)

            return cursor.fetchall()

        except Error as e:
            print(f"SQL fetch error: {e}")
            return []

        finally:
            if cursor is not None:
                cursor.close()

    
    def fetch_checked(self, query, params=None):
        """Fetch rows and log safe database diagnostics on failure."""
        conn = self.connect()

        if conn is None:
            print(
                "Database query aborted: no database connection available.",
                flush=True,
            )
            raise RuntimeError("Database connection is unavailable.")

        cursor = None

        try:
            cursor = conn.cursor(dictionary=True)

            # Diagnose the schema used by the login query.
            if "FROM app_users" in query:
                cursor.execute("SELECT DATABASE() AS db_name")
                result = cursor.fetchone()
                print(
                    "LOGIN_DIAG: selected database = "
                    + str(result["db_name"] if result else None),
                    flush=True,
                )

                cursor.execute("SHOW TABLES LIKE 'app_users'")
                print(
                    "LOGIN_DIAG: app_users visible = "
                    + str(bool(cursor.fetchone())),
                    flush=True,
                )

            if params is not None:
                cursor.execute(query, params)
            else:
                cursor.execute(query)

            return cursor.fetchall()

        except Error as exc:
            # Log only safe error metadata, not credentials or SQL parameters.
            print(
                "Database query failed: "
                f"type={type(exc).__name__}, "
                f"errno={getattr(exc, 'errno', None)}, "
                f"sqlstate={getattr(exc, 'sqlstate', None)}, "
                f"message={str(exc)[:300]}",
                flush=True,
            )
            raise RuntimeError("Database query failed.") from None

        finally:
            if cursor is not None:
                cursor.close()

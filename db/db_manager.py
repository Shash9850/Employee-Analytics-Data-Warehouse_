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
        # Streamlit Cloud stores the certificate as text.
        # mysql-connector expects ssl_ca to point to a certificate file.
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
            # Local environments can provide a normal .pem file path.
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
        """Create and return a MySQL connection."""
        if self._connection is not None and self._connection.is_connected():
            return self._connection

        try:
            config = get_db_config()

            self._connection = mysql.connector.connect(**config)

            return self._connection

        except Error as e:
            print(f"Database connection error: {e}")
            return None

    def close(self):
        """Close the database connection."""
        if self._connection is not None and self._connection.is_connected():
            self._connection.close()
            self._connection = None

    def execute(self, query, params=None):
        """Execute INSERT, UPDATE, DELETE or other SQL statements."""
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
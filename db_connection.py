import mysql.connector
from contextlib import contextmanager
from config import Config

class Db:
    def __init__(self):
        self.connection = None
        self.cursor = None

    def __enter__(self):
        try:
            self.connection = mysql.connector.connect(
                host=Config.DB_HOST,
                user=Config.DB_USER,
                password=Config.DB_PASSWORD,
                database=Config.DB_NAME,
                port=Config.DB_PORT,
                auth_plugin='mysql_native_password',
                pool_name='mypool',  # Ensure all connections use the same pool
                pool_size=5
            )
            self.cursor = self.connection.cursor(dictionary=True)
            return self
        except mysql.connector.Error as err:
            print(f"Database connection failed: {err}")
            raise

    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.cursor:
            self.cursor.close()
        if self.connection:
            if exc_type is not None:  # If an exception occurred, rollback changes
                self.rollback()
            self.connection.close()

    def execute(self, query, params=None):
        """
        Execute queries. Automatically commits if modifying the database.
        """
        try:
            self._clear_unread_results()  # Clear unread results before executing a new query
            self.cursor.execute(query, params or ())
            if query.strip().upper().startswith(("INSERT", "UPDATE", "DELETE")):
                self.connection.commit()  # Commit only for modifying queries
            return self.cursor.rowcount
        except mysql.connector.Error as err:
            self.rollback()
            print(f"Error executing query: {err}")
            raise

    def query(self, query, params=None):
        """
        Execute a SELECT query and return self for further fetching.
        """
        try:
            self._clear_unread_results()  # Clear unread results before executing a new query
            self.cursor.execute(query, params or ())
            return self
        except mysql.connector.Error as err:
            print(f"Query execution error: {err}")
            raise

    def fetchone(self):
        """Fetch a single result from the last executed query."""
        return self.cursor.fetchone() if self.cursor.with_rows else None

    def fetchall(self):
        """Fetch all results from the last executed query."""
        return self.cursor.fetchall() if self.cursor.with_rows else []

    def rollback(self):
        """Rollback the current transaction."""
        if self.connection:
            try:
                self.connection.rollback()
            except mysql.connector.Error as err:
                print(f"Error during rollback: {err}")

    def _clear_unread_results(self):
        """Clear unread results from previous queries to avoid errors."""
        try:
            while self.cursor.nextset():
                pass
        except mysql.connector.Error:
            pass  # No unread results to clear

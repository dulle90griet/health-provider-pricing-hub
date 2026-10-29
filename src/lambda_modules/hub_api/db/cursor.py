"""Provides the DatabaseCursor class and a global db_manager instance."""

from psycopg.rows import dict_row
from hub_api.db.manager import DatabaseManager


# Global instance persists across warm starts
db_manager = DatabaseManager()


class DatabaseCursor:
    """
    Context manager class for RDS database operations.

    The underlying db connection and connection pooling are managed
    by the DatabaseManager class. For retrieval of RDS connection
    details from AWS Secrets Manager, DatabaseManager depends on the
    following setup:

        RDS db master user secret:
            Created and managed by RDS.
        RDS connection details secret:
            Created and managed by the developer. Must contain a
            stringified JSON object with the keys `host`, `port`,
            `dbname` and `user_secret`, where `user_secret` is the
            ARN of the RDS db instance's master user secret.
        RDS_LOGIN_SECRET env var:
            Exported locally in the execution environment. Equal to
            the name of the RDS connection details secret.
    """

    def __init__(self, row_factory=None):
        self.conn_context = None
        self.connection = None
        self.cursor = None
        self.row_factory = row_factory or dict_row

    def __enter__(self):
        # Get connection from pool
        self.conn_context = db_manager.get_connection()
        self.connection = self.conn_context.__enter__()

        self.cursor = self.connection.cursor(row_factory=self.row_factory)
        return self.cursor

    def __exit__(self, exc_type, exc_val, exc_tb):
        if exc_type:
            # Rollback on error
            self.connection.rollback()
        else:
            # Commit on success
            self.connection.commit()

        # Close cursor and return connection to pool
        self.cursor.close()
        self.conn_context.__exit__(exc_type, exc_val, exc_tb)
        return False  # Ensure exceptions propagate

"""Provides the DatabaseManager class used by DatabaseCursor."""

import os
import json
import psycopg_pool
import boto3
from botocore.exceptions import ClientError
from hub_api.logger import logger


class DatabaseManager:
    """
    RDS database connection manager class with connection pooling,
    AWS Secrets Manager secret retrieval and lazy connection.

    Secret retrieval depends on the existence of an env variable,
    RDS_LOGIN_SECRET, that stores the name of a secret containing
    a string JSON object of RDS connection info, with the keys `host`,
    `port`, `dbname` and `user_secret`. The value of `user_secret`
    should be the ARN of the RDS db instance's master user secret.
    """

    def __init__(self):
        self._connection_pool = None
        self._connection = None
        self._secret_cache = None

    def _get_secrets(self):
        """Fetch secrets from Secrets Manager with caching"""
        if self._secret_cache is None:
            # Logic to fetch RDS connection details using SSM Secret
            # TO BE MODULARIZED
            secrets_manager = boto3.client("secretsmanager")
            logger.info("Fetching RDS login secret")
            try:
                rds_secret = secrets_manager.get_secret_value(
                    SecretId=os.environ["RDS_LOGIN_SECRET"]
                )
                rds_secret_json = json.loads(rds_secret["SecretString"])
            except ClientError as e:
                logger.error("Failed to fetch first secret: %s", e)
                raise
            logger.info("Fetching RDS master user secret")
            try:
                rds_user_secret = secrets_manager.get_secret_value(
                    SecretId=rds_secret_json["user_secret"]
                )
                rds_user_secret_json = json.loads(rds_user_secret["SecretString"])
                self._secret_cache = {
                    "host": rds_secret_json["host"],
                    "port": rds_secret_json["port"],
                    "dbname": rds_secret_json["dbname"],
                    "user": rds_user_secret_json["username"],
                    "password": rds_user_secret_json["password"],
                }
            except ClientError as e:
                logger.error("Failed to fetch second secret: %s", e)
                raise

        return self._secret_cache

    def _init_pool(self):
        """Initialize connection pool"""
        if self._connection_pool is None:
            config = self._get_secrets()

            conninfo = " ".join(f"{key}={value}" for key, value in config.items())
            self._connection_pool = psycopg_pool.ConnectionPool(
                conninfo=conninfo,
                min_size=1,
                max_size=20,
                open=True,  # Open the pool immediately
            )

            logger.info("Database connection initialized")

    def get_connection(self):
        """Get a connection from the pool"""
        self._init_pool()

        logger.info("Getting a connection from the pool")
        return self._connection_pool.connection()

    def close_all(self):
        """Close all connections in the pool"""
        if self._connection_pool:
            self._connection_pool.close()
            logger.info("All database connections closed")

from dotenv import load_dotenv

load_dotenv()

import os
import logging

try:
    import mysql.connector as mysql_connector
    from mysql.connector import Error as MySQLError
except ModuleNotFoundError:
    mysql_connector = None
    MySQLError = Exception


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def get_db_connection():
    if mysql_connector is None:
        logger.error(
            "mysql-connector-python is not installed. "
            "Install it with: pip install mysql-connector-python"
        )
        return None

    try:
        connection = mysql_connector.connect(
            host=os.getenv("DB_HOST", "localhost"),
            user=os.getenv("DB_USER", "root"),
            password=os.getenv("DB_PASSWORD", "password"),
            database=os.getenv("DB_NAME", "agentic_ai"),
        )
        if connection and connection.is_connected():
            logger.info("Database connection established.")
            return connection
        logger.warning("Database connection not established.")
        return None
    except MySQLError as e:
        logger.error(f"Database connection error: {e}")
        return None

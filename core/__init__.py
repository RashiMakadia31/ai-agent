from dotenv import load_dotenv
load_dotenv()  # ✅ Load .env variables at runtime

import mysql.connector
from mysql.connector import Error
import os
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def get_db_connection():
    try:
        connection = mysql.connector.connect(
            host=os.getenv("DB_HOST", "localhost"),
            user=os.getenv("DB_USER", "root"),
            password=os.getenv("DB_PASSWORD", "password"),
            database=os.getenv("DB_NAME", "agentic_ai")
        )
        if connection and connection.is_connected():
            logger.info("✅ Database connection established.")
            return connection
        else:
            logger.warning("⚠️ Database connection not established.")
            return None
    except Error as e:
        logger.error(f"❌ Database connection error: {e}")
        return None

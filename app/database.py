import os
import time
import logging
import mysql.connector

from typing import Optional
from dotenv import load_dotenv
from mysql.connector import Error

# Load environment variables
load_dotenv()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class DatabaseConnectionError(Exception):
    """Custom exception for database connection failures"""

    pass

def get_db_connection(
    max_retries: int = 12,  # 12 retries = 1 minute total (12 * 5 seconds)
    retry_delay: int = 5,  # 5 seconds between retries
) -> mysql.connector.MySQLConnection:
    """Create database connection with retry mechanism."""
    connection: Optional[mysql.connector.MySQLConnection] = None
    attempt = 1
    last_error = None

    while attempt <= max_retries:
        try:
            connection = mysql.connector.connect(
                host=os.getenv("MYSQL_HOST"),
                user=os.getenv("MYSQL_USER"),
                password=os.getenv("MYSQL_PASSWORD"),
                database=os.getenv("MYSQL_DATABASE"),
            )

            # Test the connection
            connection.ping(reconnect=True, attempts=1, delay=0)
            logger.info("Database connection established successfully")
            return connection

        except Error as err:
            last_error = err
            logger.warning(
                f"Connection attempt {attempt}/{max_retries} failed: {err}. "
                f"Retrying in {retry_delay} seconds..."
            )

            if connection is not None:
                try:
                    connection.close()
                except Exception:
                    pass

            if attempt == max_retries:
                break

            time.sleep(retry_delay)
            attempt += 1

    raise DatabaseConnectionError(
        f"Failed to connect to database after {max_retries} attempts. "
        f"Last error: {last_error}"
    )


async def setup_database(initial_users: dict = None):
    """Creates user and session tables and populates initial user data if provided."""
    connection = None
    cursor = None

    # Define table schemas
    table_schemas = {
        "users": """
            CREATE TABLE users (
                id INT AUTO_INCREMENT PRIMARY KEY,
                fullname VARCHAR(255) NOT NULL,
                username VARCHAR(255) NOT NULL UNIQUE,
                password VARCHAR(255) NOT NULL,
                location VARCHAR(255) NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """,
        "sessions": """
            CREATE TABLE sessions (
                id VARCHAR(36) PRIMARY KEY,
                user_id INT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
            )
        """,
    }

    try:
        # Get database connection
        connection = get_db_connection()
        cursor = connection.cursor()

        # Drop and recreate tables one by one
        for table_name in ["sessions", "users"]:
            # Drop table if exists
            logger.info(f"Dropping table {table_name} if exists...")
            cursor.execute(f"DROP TABLE IF EXISTS {table_name}")
            connection.commit()

        # Recreate tables one by one
        for table_name, create_query in table_schemas.items():

            try:
                # Create table
                logger.info(f"Creating table {table_name}...")
                cursor.execute(create_query)
                connection.commit()
                logger.info(f"Table {table_name} created successfully")

            except Error as e:
                logger.error(f"Error creating table {table_name}: {e}")
                raise

        # Insert initial users if provided
        if initial_users:
            try:
                insert_query = """
                    INSERT INTO users (fullname, username, password, location) 
                    VALUES (%s, %s, %s, %s) 
                    ON DUPLICATE KEY UPDATE username=username
                """
                for user in initial_users:
                    cursor.execute(insert_query, (user["fullname"], user["username"], user["password"], user["location"]))
                connection.commit()
                logger.info(f"Inserted {len(initial_users)} initial users")
                
            except Error as e:
                logger.error(f"Error inserting initial users: {e}")
                raise

    except Exception as e:
        logger.error(f"Database setup failed: {e}")
        raise

    finally:
        if cursor:
            cursor.close()
        if connection and connection.is_connected():
            connection.close()
            logger.info("Database connection closed")


# Database utility functions for user and session management
async def get_user_by_username(username: str) -> Optional[dict]:
    """Retrieve user from database by username."""
    connection = None
    cursor = None
    try:
        connection = get_db_connection()
        cursor = connection.cursor(dictionary=True)
        cursor.execute("SELECT id, fullname, username, password, location FROM users WHERE username = %s", (username,))
        return cursor.fetchone()
    finally:
        if cursor:
            cursor.close()
        if connection and connection.is_connected():
            connection.close()


async def get_user_by_id(user_id: int) -> Optional[dict]:
    """
    Retrieve user from database by ID.

    Args:
        user_id: The ID of the user to retrieve

    Returns:
        Optional[dict]: User data if found, None otherwise
    """
    connection = None
    cursor = None
    try:
        connection = get_db_connection()
        cursor = connection.cursor(dictionary=True)
        cursor.execute("SELECT * FROM users WHERE id = %s", (user_id,))
        return cursor.fetchone()
    finally:
        if cursor:
            cursor.close()
        if connection and connection.is_connected():
            connection.close()


async def create_session(user_id: int, session_id: str) -> bool:
    """Create a new session in the database."""
    connection = None
    cursor = None
    try:
        connection = get_db_connection()
        cursor = connection.cursor()
        cursor.execute(
            "INSERT INTO sessions (id, user_id) VALUES (%s, %s)", (session_id, user_id)
        )
        connection.commit()
        return True
    finally:
        if cursor:
            cursor.close()
        if connection and connection.is_connected():
            connection.close()


async def get_session(session_id: str) -> Optional[dict]:
    """Retrieve session from database."""
    connection = None
    cursor = None
    try:
        connection = get_db_connection()
        cursor = connection.cursor(dictionary=True)
        cursor.execute(
            """
            SELECT *
            FROM sessions s
            WHERE s.id = %s
        """,
            (session_id,),
        )
        return cursor.fetchone()
    finally:
        if cursor:
            cursor.close()
        if connection and connection.is_connected():
            connection.close()


async def delete_session(session_id: str) -> bool:
    """Delete a session from the database."""
    connection = None
    cursor = None
    try:
        connection = get_db_connection()
        cursor = connection.cursor()
        cursor.execute("DELETE FROM sessions WHERE id = %s", (session_id,))
        connection.commit()
        return True
    finally:
        if cursor:
            cursor.close()
        if connection and connection.is_connected():
            connection.close()






async def create_user(fullname: str, username: str, password: str, location: str) -> bool:
    """Creates a new user and saves to the database without password hashing."""
    connection = None
    cursor = None
    try:
        connection = get_db_connection()
        cursor = connection.cursor()
        cursor.execute(
            "INSERT INTO users (fullname, username, password, location) VALUES (%s, %s, %s, %s)",
            (fullname, username, password, location)
        )
        connection.commit()
        return True
    except Error as e:
        logger.error(f"Error inserting new user: {e}")
        return False
    finally:
        if cursor:
            cursor.close()
        if connection and connection.is_connected():
            connection.close()
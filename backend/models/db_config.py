import sqlite3
from sqlite3 import Error
import os

def get_db_connection():
    """Create and return a SQLite database connection"""
    db_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'database', 'smartar.db')
    try:
        connection = sqlite3.connect(db_path)
        # Enable WAL mode for better concurrency
        connection.execute("PRAGMA journal_mode=WAL;")
        connection.execute("PRAGMA synchronous=NORMAL;")
        
        # Enable row factory to access columns by name
        connection.row_factory = sqlite3.Row
        return connection
    except Error as e:
        print(f"Error connecting to SQLite: {e}")
        return None

def close_connection(connection, db_query=None):
    """Close the database connection and the query executor"""
    if db_query:
        db_query.close()
    if connection:
        connection.close()

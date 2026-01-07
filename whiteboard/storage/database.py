"""
Database operations for whiteboard storage
"""

import sqlite3
import json
from datetime import datetime


class Database:
    """
    Handles SQLite database operations for whiteboard objects
    """

    SCHEMA_VERSION = 1

    def __init__(self, db_path):
        """
        Initialize database connection

        Args:
            db_path: Path to SQLite database file
        """
        self.db_path = db_path
        self.conn = None

    def connect(self):
        """Open database connection"""
        self.conn = sqlite3.connect(self.db_path)
        self.conn.row_factory = sqlite3.Row

    def close(self):
        """Close database connection"""
        if self.conn:
            self.conn.close()
            self.conn = None

    def create_schema(self):
        """Create database schema"""
        cursor = self.conn.cursor()

        # Metadata table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS board_metadata (
                key TEXT PRIMARY KEY,
                value TEXT
            )
        ''')

        # Objects table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS objects (
                id TEXT PRIMARY KEY,
                type TEXT NOT NULL,
                x REAL NOT NULL,
                y REAL NOT NULL,
                width REAL NOT NULL,
                height REAL NOT NULL,
                z_index INTEGER NOT NULL,
                data TEXT NOT NULL,
                created_at INTEGER NOT NULL,
                modified_at INTEGER NOT NULL
            )
        ''')

        # Indexes for performance
        cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_objects_position
            ON objects(x, y)
        ''')

        cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_objects_z_index
            ON objects(z_index)
        ''')

        # Store schema version
        cursor.execute('''
            INSERT OR REPLACE INTO board_metadata (key, value)
            VALUES ('schema_version', ?)
        ''', (str(self.SCHEMA_VERSION),))

        # Store creation timestamp
        cursor.execute('''
            INSERT OR IGNORE INTO board_metadata (key, value)
            VALUES ('created_at', ?)
        ''', (str(int(datetime.now().timestamp())),))

        self.conn.commit()

    def save_objects(self, objects):
        """
        Save objects to database

        Args:
            objects: List of canvas objects to save
        """
        cursor = self.conn.cursor()

        # Clear existing objects
        cursor.execute('DELETE FROM objects')

        # Insert objects
        for obj in objects:
            obj_dict = obj.to_dict()

            # Create timestamps if not present
            now = int(datetime.now().timestamp())
            created_at = obj_dict.get('created_at', now)
            modified_at = now

            cursor.execute('''
                INSERT INTO objects
                (id, type, x, y, width, height, z_index, data, created_at, modified_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                obj_dict['id'],
                obj_dict['type'],
                obj_dict['x'],
                obj_dict['y'],
                obj_dict['width'],
                obj_dict['height'],
                obj_dict['z_index'],
                obj_dict['data'],
                created_at,
                modified_at
            ))

        # Update last modified timestamp
        cursor.execute('''
            INSERT OR REPLACE INTO board_metadata (key, value)
            VALUES ('modified_at', ?)
        ''', (str(int(datetime.now().timestamp())),))

        self.conn.commit()

    def load_objects(self):
        """
        Load objects from database

        Returns:
            List of object dictionaries
        """
        cursor = self.conn.cursor()

        cursor.execute('''
            SELECT id, type, x, y, width, height, z_index, data,
                   created_at, modified_at
            FROM objects
            ORDER BY z_index
        ''')

        objects = []
        for row in cursor.fetchall():
            obj_dict = {
                'id': row['id'],
                'type': row['type'],
                'x': row['x'],
                'y': row['y'],
                'width': row['width'],
                'height': row['height'],
                'z_index': row['z_index'],
                'data': row['data'],
                'created_at': row['created_at'],
                'modified_at': row['modified_at']
            }
            objects.append(obj_dict)

        return objects

    def get_metadata(self, key):
        """
        Get metadata value

        Args:
            key: Metadata key

        Returns:
            Metadata value or None
        """
        cursor = self.conn.cursor()
        cursor.execute('SELECT value FROM board_metadata WHERE key = ?', (key,))
        row = cursor.fetchone()
        return row['value'] if row else None

    def set_metadata(self, key, value):
        """
        Set metadata value

        Args:
            key: Metadata key
            value: Metadata value
        """
        cursor = self.conn.cursor()
        cursor.execute('''
            INSERT OR REPLACE INTO board_metadata (key, value)
            VALUES (?, ?)
        ''', (key, value))
        self.conn.commit()

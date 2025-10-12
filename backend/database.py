"""
Database utilities and connection management
"""
import aiosqlite
import os
from pathlib import Path


class Database:
    """Database connection manager"""

    def __init__(self, db_path: str):
        self.db_path = db_path
        self.connection = None

    async def connect(self):
        """Establish database connection"""
        # Ensure directory exists
        db_dir = Path(self.db_path).parent
        db_dir.mkdir(parents=True, exist_ok=True)

        self.connection = await aiosqlite.connect(self.db_path)
        self.connection.row_factory = aiosqlite.Row

        # Initialize tables
        await self._init_tables()

    async def disconnect(self):
        """Close database connection"""
        if self.connection:
            await self.connection.close()

    async def _init_tables(self):
        """Initialize database tables"""
        async with self.connection.cursor() as cursor:
            # Projects table
            await cursor.execute("""
                CREATE TABLE IF NOT EXISTS projects (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL,
                    width INTEGER NOT NULL,
                    height INTEGER NOT NULL,
                    fps INTEGER NOT NULL,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                )
            """)

            # Frames table
            await cursor.execute("""
                CREATE TABLE IF NOT EXISTS frames (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    path TEXT NOT NULL,
                    generator TEXT NOT NULL,
                    project_id INTEGER NOT NULL,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL,
                    FOREIGN KEY (project_id) REFERENCES projects (id) ON DELETE CASCADE
                )
            """)

            # Create index for faster lookups by project_id
            await cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_frames_project_id ON frames (project_id)
            """)

            # Tasks table (for generator system)
            await cursor.execute("""
                CREATE TABLE IF NOT EXISTS tasks (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL,
                    type TEXT NOT NULL,
                    data TEXT NOT NULL,
                    status TEXT NOT NULL DEFAULT 'pending',
                    progress REAL NOT NULL DEFAULT 0.0,
                    result TEXT,
                    error TEXT,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL,
                    started_at TEXT,
                    completed_at TEXT
                )
            """)

            # Create index for faster lookups by status
            await cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_tasks_status ON tasks (status)
            """)

            # Create index for faster lookups by type
            await cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_tasks_type ON tasks (type)
            """)

            # Example: Create a simple users table
            await cursor.execute("""
                CREATE TABLE IF NOT EXISTS users (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    username TEXT UNIQUE NOT NULL,
                    email TEXT UNIQUE NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)

            # Example: Create a sessions table
            await cursor.execute("""
                CREATE TABLE IF NOT EXISTS sessions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL,
                    session_token TEXT UNIQUE NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    expires_at TIMESTAMP NOT NULL,
                    FOREIGN KEY (user_id) REFERENCES users (id)
                )
            """)

            await self.connection.commit()

    async def execute(self, query: str, params: tuple = ()):
        """Execute a query"""
        async with self.connection.cursor() as cursor:
            await cursor.execute(query, params)
            await self.connection.commit()
            return cursor.lastrowid

    async def fetch_one(self, query: str, params: tuple = ()):
        """Fetch one row"""
        async with self.connection.cursor() as cursor:
            await cursor.execute(query, params)
            return await cursor.fetchone()

    async def fetch_all(self, query: str, params: tuple = ()):
        """Fetch all rows"""
        async with self.connection.cursor() as cursor:
            await cursor.execute(query, params)
            return await cursor.fetchall()


# Global database instance
db: Database = None


def get_db() -> Database:
    """Get database instance"""
    return db


async def init_db(db_path: str):
    """Initialize database"""
    global db
    db = Database(db_path)
    await db.connect()
    return db


async def close_db():
    """Close database"""
    global db
    if db:
        await db.disconnect()


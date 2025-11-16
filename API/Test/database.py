# CHANGED: Created database abstraction layer with TWO connection methods

"""
DATABASE CONNECTION METHOD 1: SQLAlchemy ORM (Recommended for complex apps)
Pros: Object-relational mapping, migrations, easier queries
Cons: Slightly more overhead, learning curve
"""

from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

db = SQLAlchemy()

class Note(db.Model):
    """Note model using SQLAlchemy ORM"""
    __tablename__ = 'notes'
    
    id = db.Column(db.Integer, primary_key=True)
    content = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def to_dict(self):
        """Convert model to dictionary"""
        return {
            'id': self.id,
            'content': self.content,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat()
        }
    
    def __repr__(self):
        return f'<Note {self.id}>'


"""
DATABASE CONNECTION METHOD 2: psycopg2 with Connection Pool (Recommended for simple apps)
Pros: Lightweight, direct SQL control, faster for simple queries
Cons: Manual SQL writing, no ORM benefits
"""

# import psycopg2
# from psycopg2 import pool
# from contextlib import contextmanager

# class DatabasePool:
#     """Database connection pool manager"""
#     _pool = None
    
#     @classmethod
#     def initialize(cls, config):
#         """Initialize connection pool"""
#         if cls._pool is None:
#             cls._pool = psycopg2.pool.ThreadedConnectionPool(
#                 config.DATABASE_POOL_MIN,
#                 config.DATABASE_POOL_MAX,
#                 host=config.DB_HOST,
#                 port=config.DB_PORT,
#                 database=config.DB_NAME,
#                 user=config.DB_USER,
#                 password=config.DB_PASSWORD
#             )
    
#     @classmethod
#     @contextmanager
#     def get_connection(cls):
#         """Context manager for database connections"""
#         conn = cls._pool.getconn()
#         try:
#             yield conn
#             conn.commit()
#         except Exception as e:
#             conn.rollback()
#             raise e
#         finally:
#             cls._pool.putconn(conn)
    
#     @classmethod
#     def close_all(cls):
#         """Close all connections in pool"""
#         if cls._pool:
#             cls._pool.closeall()


# # Database operations using psycopg2 (Method 2)
# class NoteRepository:
#     """Repository pattern for Note operations"""
    
#     @staticmethod
#     def create(content):
#         """Create a new note"""
#         with DatabasePool.get_connection() as conn:
#             with conn.cursor() as cur:
#                 cur.execute(
#                     "INSERT INTO notes (content, created_at) VALUES (%s, %s) RETURNING id, content, created_at",
#                     (content, datetime.utcnow())
#                 )
#                 row = cur.fetchone()
#                 return {'id': row[0], 'content': row[1], 'created_at': row[2].isoformat()}
    
#     @staticmethod
#     def get_all():
#         """Get all notes"""
#         with DatabasePool.get_connection() as conn:
#             with conn.cursor() as cur:
#                 cur.execute("SELECT id, content, created_at FROM notes ORDER BY created_at DESC")
#                 rows = cur.fetchall()
#                 return [{'id': r[0], 'content': r[1], 'created_at': r[2].isoformat()} for r in rows]
    
#     @staticmethod
#     def get_by_id(note_id):
#         """Get note by ID"""
#         with DatabasePool.get_connection() as conn:
#             with conn.cursor() as cur:
#                 cur.execute("SELECT id, content, created_at FROM notes WHERE id = %s", (note_id,))
#                 row = cur.fetchone()
#                 if row:
#                     return {'id': row[0], 'content': row[1], 'created_at': row[2].isoformat()}
#                 return None
    
#     @staticmethod
#     def update(note_id, content):
#         """Update note"""
#         with DatabasePool.get_connection() as conn:
#             with conn.cursor() as cur:
#                 cur.execute(
#                     "UPDATE notes SET content = %s, updated_at = %s WHERE id = %s RETURNING id, content",
#                     (content, datetime.utcnow(), note_id)
#                 )
#                 row = cur.fetchone()
#                 if row:
#                     return {'id': row[0], 'content': row[1]}
#                 return None
    
#     @staticmethod
#     def delete(note_id):
#         """Delete note"""
#         with DatabasePool.get_connection() as conn:
#             with conn.cursor() as cur:
#                 cur.execute("DELETE FROM notes WHERE id = %s", (note_id,))
#                 return cur.rowcount > 0
    
#     @staticmethod
#     def search(query):
#         """Search notes"""
#         with DatabasePool.get_connection() as conn:
#             with conn.cursor() as cur:
#                 cur.execute(
#                     "SELECT id, content, created_at FROM notes WHERE content ILIKE %s ORDER BY created_at DESC",
#                     (f'%{query}%',)
#                 )
#                 rows = cur.fetchall()
#                 return [{'id': r[0], 'content': r[1], 'created_at': r[2].isoformat()} for r in rows]

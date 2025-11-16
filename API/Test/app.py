# CHANGED: Renamed file from tet.py to app.py for clarity
# CHANGED: Added Flask framework and PostgreSQL connection
# CHANGED: Added basic CRUD endpoints for notes

from flask import Flask, render_template, request, jsonify
import datetime
import psycopg2
from psycopg2 import pool
import os

app = Flask(__name__)

# CHANGED: Added database connection pool (simple approach)
# Connection pool prevents opening/closing DB connections repeatedly
db_pool = None

def init_db_pool():
    """Initialize database connection pool"""
    global db_pool
    db_pool = psycopg2.pool.SimpleConnectionPool(
        1, 10,  # Min and max connections
        host="localhost",
        database="notes_db",
        user="postgres",
        password="your_password"
    )

# CHANGED: Added route for homepage
@app.route('/')
def index():
    """Serve the main HTML page"""
    return render_template('test.html')

# CHANGED: Added CREATE endpoint
@app.route('/api/notes', methods=['POST'])
def create_note():
    """Create a new note - Status Code: 201 (Created)"""
    try:
        data = request.get_json()
        content = data.get('content', '')
        
        conn = db_pool.getconn()
        cur = conn.cursor()
        cur.execute(
            "INSERT INTO notes (content, created_at) VALUES (%s, %s) RETURNING id",
            (content, datetime.datetime.now())
        )
        note_id = cur.fetchone()[0]
        conn.commit()
        cur.close()
        db_pool.putconn(conn)
        
        return jsonify({'id': note_id, 'content': content}), 201
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# CHANGED: Added READ ALL endpoint
@app.route('/api/notes', methods=['GET'])
def get_notes():
    """Get all notes - Status Code: 200 (OK)"""
    try:
        conn = db_pool.getconn()
        cur = conn.cursor()
        cur.execute("SELECT id, content, created_at FROM notes ORDER BY created_at DESC")
        notes = cur.fetchall()
        cur.close()
        db_pool.putconn(conn)
        
        result = [{'id': n[0], 'content': n[1], 'created_at': str(n[2])} for n in notes]
        return jsonify(result), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# CHANGED: Added READ ONE endpoint
@app.route('/api/notes/<int:note_id>', methods=['GET'])
def get_note(note_id):
    """Get single note - Status Code: 200 (OK) or 404 (Not Found)"""
    try:
        conn = db_pool.getconn()
        cur = conn.cursor()
        cur.execute("SELECT id, content, created_at FROM notes WHERE id = %s", (note_id,))
        note = cur.fetchone()
        cur.close()
        db_pool.putconn(conn)
        
        if note:
            return jsonify({'id': note[0], 'content': note[1], 'created_at': str(note[2])}), 200
        return jsonify({'error': 'Note not found'}), 404
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# CHANGED: Added UPDATE endpoint
@app.route('/api/notes/<int:note_id>', methods=['PUT'])
def update_note(note_id):
    """Update note - Status Code: 200 (OK) or 404 (Not Found)"""
    try:
        data = request.get_json()
        content = data.get('content', '')
        
        conn = db_pool.getconn()
        cur = conn.cursor()
        cur.execute("UPDATE notes SET content = %s WHERE id = %s", (content, note_id))
        rows_affected = cur.rowcount
        conn.commit()
        cur.close()
        db_pool.putconn(conn)
        
        if rows_affected > 0:
            return jsonify({'id': note_id, 'content': content}), 200
        return jsonify({'error': 'Note not found'}), 404
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# CHANGED: Added DELETE endpoint
@app.route('/api/notes/<int:note_id>', methods=['DELETE'])
def delete_note(note_id):
    """Delete note - Status Code: 204 (No Content) or 404 (Not Found)"""
    try:
        conn = db_pool.getconn()
        cur = conn.cursor()
        cur.execute("DELETE FROM notes WHERE id = %s", (note_id,))
        rows_affected = cur.rowcount
        conn.commit()
        cur.close()
        db_pool.putconn(conn)
        
        if rows_affected > 0:
            return '', 204
        return jsonify({'error': 'Note not found'}), 404
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# CHANGED: Added search endpoint
@app.route('/api/notes/search', methods=['GET'])
def search_notes():
    """Search notes - Status Code: 200 (OK)"""
    try:
        query = request.args.get('q', '')
        conn = db_pool.getconn()
        cur = conn.cursor()
        cur.execute(
            "SELECT id, content, created_at FROM notes WHERE content ILIKE %s ORDER BY created_at DESC",
            (f'%{query}%',)
        )
        notes = cur.fetchall()
        cur.close()
        db_pool.putconn(conn)
        
        result = [{'id': n[0], 'content': n[1], 'created_at': str(n[2])} for n in notes]
        return jsonify(result), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    init_db_pool()  # CHANGED: Initialize DB connection on startup
    app.run(debug=True, port=5000)

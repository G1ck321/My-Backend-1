# CHANGED: Separated routes into blueprint for better organization
from flask import Blueprint, request, jsonify
from database import Note, db, NoteRepository
from datetime import datetime

notes_bp = Blueprint('notes', __name__, url_prefix='/api/notes')

"""
Choose ONE implementation below based on your database method:
- Use Method 1 (SQLAlchemy) for better ORM features
- Use Method 2 (psycopg2) for simpler, lighter implementation
"""

# ========== METHOD 1: SQLAlchemy ORM Implementation ==========

@notes_bp.route('', methods=['POST'])
def create_note_orm():
    """Create note using SQLAlchemy - Status 201"""
    try:
        data = request.get_json()
        
        # Validation
        if not data or 'content' not in data or not data['content'].strip():
            return jsonify({'error': 'Content is required'}), 400
        
        note = Note(content=data['content'])
        db.session.add(note)
        db.session.commit()
        
        return jsonify(note.to_dict()), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@notes_bp.route('', methods=['GET'])
def get_notes_orm():
    """Get all notes using SQLAlchemy - Status 200"""
    try:
        notes = Note.query.order_by(Note.created_at.desc()).all()
        return jsonify([note.to_dict() for note in notes]), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@notes_bp.route('/<int:note_id>', methods=['GET'])
def get_note_orm(note_id):
    """Get single note using SQLAlchemy - Status 200 or 404"""
    try:
        note = Note.query.get(note_id)
        if note:
            return jsonify(note.to_dict()), 200
        return jsonify({'error': 'Note not found'}), 404
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@notes_bp.route('/<int:note_id>', methods=['PUT'])
def update_note_orm(note_id):
    """Update note using SQLAlchemy - Status 200 or 404"""
    try:
        note = Note.query.get(note_id)
        if not note:
            return jsonify({'error': 'Note not found'}), 404
        
        data = request.get_json()
        if not data or 'content' not in data:
            return jsonify({'error': 'Content is required'}), 400
        
        note.content = data['content']
        note.updated_at = datetime.utcnow()
        db.session.commit()
        
        return jsonify(note.to_dict()), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@notes_bp.route('/<int:note_id>', methods=['DELETE'])
def delete_note_orm(note_id):
    """Delete note using SQLAlchemy - Status 204 or 404"""
    try:
        note = Note.query.get(note_id)
        if not note:
            return jsonify({'error': 'Note not found'}), 404
        
        db.session.delete(note)
        db.session.commit()
        
        return '', 204
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@notes_bp.route('/search', methods=['GET'])
def search_notes_orm():
    """Search notes using SQLAlchemy - Status 200"""
    try:
        query = request.args.get('q', '')
        notes = Note.query.filter(Note.content.ilike(f'%{query}%')).order_by(Note.created_at.desc()).all()
        return jsonify([note.to_dict() for note in notes]), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500


# ========== METHOD 2: psycopg2 Connection Pool Implementation ==========
# Uncomment these if using Method 2 (comment out Method 1 above)

"""
@notes_bp.route('', methods=['POST'])
def create_note_psycopg2():
    try:
        data = request.get_json()
        if not data or 'content' not in data or not data['content'].strip():
            return jsonify({'error': 'Content is required'}), 400
        
        note = NoteRepository.create(data['content'])
        return jsonify(note), 201
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@notes_bp.route('', methods=['GET'])
def get_notes_psycopg2():
    try:
        notes = NoteRepository.get_all()
        return jsonify(notes), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@notes_bp.route('/<int:note_id>', methods=['GET'])
def get_note_psycopg2(note_id):
    try:
        note = NoteRepository.get_by_id(note_id)
        if note:
            return jsonify(note), 200
        return jsonify({'error': 'Note not found'}), 404
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@notes_bp.route('/<int:note_id>', methods=['PUT'])
def update_note_psycopg2(note_id):
    try:
        data = request.get_json()
        if not data or 'content' not in data:
            return jsonify({'error': 'Content is required'}), 400
        
        note = NoteRepository.update(note_id, data['content'])
        if note:
            return jsonify(note), 200
        return jsonify({'error': 'Note not found'}), 404
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@notes_bp.route('/<int:note_id>', methods=['DELETE'])
def delete_note_psycopg2(note_id):
    try:
        if NoteRepository.delete(note_id):
            return '', 204
        return jsonify({'error': 'Note not found'}), 404
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@notes_bp.route('/search', methods=['GET'])
def search_notes_psycopg2():
    try:
        query = request.args.get('q', '')
        notes = NoteRepository.search(query)
        return jsonify(notes), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500
"""

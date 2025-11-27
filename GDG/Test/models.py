# from flask_sqlalchemy import SQLAlchemy
# from datetime import datetime


# db = SQLAlchemy()
# class Note(db.Model):
#     """Note Model using SQLAlchemy ORM"""
#     __tablename__ = 'note'
#     id = db.Column(db.Integer, primary_key=True)
#     content = db.Column(db.Text, nullable=False)
#     created_at = db.Column(db.DateTime, default=datetime.utcnow)
#     updated_at = db.Column(db.DateTime, default = datetime.utcnow)
    
#     def to_dictionary(self):
#         """Convert Database model to dictionary"""
#         return{
#             'id': self.id,
#             'content': self.content,
#             'created_at':self.created_at.isoformat(),
#             'updated_at': self.updated_at.isoformat()
#         }
        
#     def __repr__(self):
#         return f'<Note {self.id}>'
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

class User(db.Model):
    """Note Model"""
    __tablename__ = 'onboard'
    id = db.Column(db.Integer,primary_key = True)
    name = db.Column(db.Text,primary_key = False, nullable = False)
    email = db.Column(db.Text, primary_key = True)
    
    def to_dictionary(self):
        return {
            'id':self.id,
            'name':self.name,
            'surname':self.surname
        }
        
    
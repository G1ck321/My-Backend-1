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
        
    
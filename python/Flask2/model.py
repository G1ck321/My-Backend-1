from flask_sqlalchemy import SQLAlchemy
from config import  db




class User(db.Model):
    id = db.Column(db.Integer, primary_key = True)
    age = db.Column(db.Integer,unique=False ,nullable=False)
    job = db.Column(db.VARCHAR(200),unique =False  ,nullable=False)
    username = db.Column(db.VARCHAR(200),unique =True  ,nullable=False)
    def to_json(self):
        return{
            'id' : self.id,
            'age':self.age,
            'job':self.job,
            'username':self.username
        }
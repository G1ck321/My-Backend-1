#It's best to go from config to the actual data(models)

from config import db

class Contact (db.Model):
    id = db.Column(db.Integer, primary_key = True)
    first_name = db.Column(db.String(80),unique = False, nullable = False)
    last_name = db.Column(db.String(80),unique = False, nullable = False)
    email = db.Column(db.String(80),unique = True, nullable = False)
    #Unique means no two emails can be the same or 400 request is return
    #means you can not pass a null value.
    
    def to_json(self):
        """"Allows us convert the fields to JSON
        camelCase is the best for JSON object values use snake_casing"""
        return {
            "id":self.id,
            "firstName":self.first_name,
            "lastName":self.last_name,
            "email":self.email
        }
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS
        

app = Flask(__name__)
CORS(app)
app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://postgres:Sampled321@localhost:5432/notes'
#specifies a path to the database. 
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
#does not track modifications


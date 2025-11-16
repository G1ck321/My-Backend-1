from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS

app = Flask(__name__)
CORS(app)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///site.db'
#specifies a path to the database. 
app.config["SQLALCHEMY_TRACK__MODIFICATIONS"] = False
#does not track modifications

db = SQLAlchemy(app)
#creates database instance

from flask_sqlalchemy import SQLAlchemy
from flask import Flask
from flask_cors import CORS

app = Flask(__name__)

CORS(app)

app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://postgres:Sampled321@localhost:5432/onboard'
#database path
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
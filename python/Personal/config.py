from flask_sqlalchemy import SQLAlchemy
from flask import Flask
from flask_cors import CORS
from dotenv import load_dotenv
import os

load_dotenv()

app = Flask(__name__)

CORS(app)
URI = os.getenv('URI')
app.config['SQLALCHEMY_DATABASE_URI'] = URI
#database path
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS
from dotenv import load_dotenv
from sqlalchemy import create_engine,table
import os

load_dotenv()

DB_HOST = os.getenv('DB_HOST')
DB_PORT = os.getenv('DB_PORT')
DB_USER = os.getenv('DB_USER')
DB_NAME = os.getenv('DB_NAME')
DB_PASSWORD = os.getenv('DB_PASSWORD')
URI = "postgresql://googledeveloper:of1aTtbfExgy87T4Y3HeSmfob4i8syB3@dpg-d4cv3mggjchc73dlqgdg-a/notes_r71t"

app = Flask(__name__)
CORS(app)

# app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://googledeveloper:of1aTtbfExgy87T4Y3HeSmfob4i8syB3@dpg-d4cv3mggjchc73dlqgdg-a/notes_r71t'
app.config['SQLALCHEMY_DATABASE_URI'] = URI
#specifies a path to the database. 
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
#does not track modifications
engine = create_engine(URI)
con = engine.connect()


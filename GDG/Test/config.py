from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS
from dotenv import load_dotenv

import os

load_dotenv()

DB_HOST = os.getenv('DB_HOST')
DB_PORT = os.getenv('DB_PORT')
DB_USER = os.getenv('DB_USER')
DB_NAME = os.getenv('DB_NAME')
DB_PASSWORD = os.getenv('DB_PASSWORD')
URI = os.getenv('URI')
# URI = "postgresql+psycopg2://neondb_owner:npg_f7M0DTwgPOan@ep-mute-mouse-abu9a6ai-pooler.eu-west-2.aws.neon.tech/neondb?sslmode=require&channel_binding=require"
# URI = "postgresql://googledeveloper:of1aTtbfExgy87T4Y3HeSmfob4i8syB3@dpg-d4cv3mggjchc73dlqgdg-a/notes_r71t"
# URI= 'postgresql://postgres:Sampled321@localhost:5432/notes'
app = Flask(__name__)
CORS(app)

# app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://googledeveloper:of1aTtbfExgy87T4Y3HeSmfob4i8syB3@dpg-d4cv3mggjchc73dlqgdg-a/notes_r71t'
app.config['SQLALCHEMY_DATABASE_URI'] = URI
#specifies a path to the database. 
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
#does not track modifications



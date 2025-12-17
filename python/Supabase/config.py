from flask_sqlalchemy import SQLAlchemy
from flask import Flask
from flask_cors import CORS
import os
from dotenv import load_dotenv
from supabase import create_client, Client

load_dotenv()
app = Flask(__name__)

CORS(app)

url = os.getenv("SUPABASE_URL")
key = os.getenv("SUPABASE_KEY")
tablename = os.getenv("TABLE_NAME")

supabase = create_client(url,key)

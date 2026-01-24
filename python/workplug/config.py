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
key = os.getenv("ANON_KEY")
news_key = os.getenv("NEWS_API_KEY","")

# tablename = os.getenv("TABLE_NAME")
# print(url)
# print(key)
supabase = create_client(url,key)

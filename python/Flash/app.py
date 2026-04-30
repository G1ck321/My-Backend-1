
from flask import Flask,flash,redirect, render_template, request,url_for
app = Flask(__name__)

app.secret_key='some_secret'
@app.route('/')
def index():
    return render_template('index.html')
    

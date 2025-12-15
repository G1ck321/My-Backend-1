from flask import Flask, jsonify, request,render_template
from config import app
from model import db,User

users = []
with app.app_context():
    db.init_app(app)
    
    db.create_all()
    
@app.route("/")
def home():
    return render_template("index.html")
@app.route("/submit",methods=["POST"])
def subMit():
    data = request.form.get('name')
    print(data)
    return render_template("index.html")
if __name__ == "__main__":
    app.run( port=5000, debug=True)
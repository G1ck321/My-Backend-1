from flask import request, jsonify
from flask_cors import CORS
from config import app
from flask_jwt_extended import  create_access_token, jwt_required


@app.route("/")
def home():
    return jsonify("Hi")

@app.route("/login", methods=["POST"])
def login(): 
    username = request.json.get("username")
    password = request.json.get("password")
    if username == "admin" and password =="secret":
        create_access_token(identity = username)
        return jsonify(access_token  = access_token)
    return jsonify({"msg": "Bad username"}),401

@app.route("/protected", methods=["GET"])
@jwt_required
def protected():
    return jsonify({"msg": "Welcome to the VIP section!"})

app.run(port = 3000)

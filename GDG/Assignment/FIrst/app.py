from flask import request, jsonify, render_template
from flask_cors import CORS
from config import app
from flask_jwt_extended import create_access_token, jwt_required, get_jwt_identity
from models import db, User


@app.route("/")
def home():
    return jsonify("Hi")


@app.route("/login-demo", methods=["GET"])
def login_demo():
    return render_template("login.html")


@app.route("/signup-demo", methods=["GET"])
def signup_demo():
    return render_template("signup.html")


@app.route("/dashboard", methods=["GET"])
def dashboard():
    return render_template("dashboard.html")

@app.route("/login", methods=["POST"])
def login():
    payload = request.get_json(silent=True) or {}
    username = (payload.get("username") or "").strip()
    password = payload.get("password") or ""

    if not username or not password:
        return jsonify({"msg": "Username and password are required"}), 400
    
    # Query user from database
    user = User.query.filter_by(username=username).first()
    
    if user and user.check_password(password):
        access_token = create_access_token(identity=username)
        return jsonify(access_token=access_token)
    return jsonify({"msg": "Bad username or password"}), 401


@app.route("/signup", methods=["POST"])
def signup():
    payload = request.get_json(silent=True) or {}
    username = (payload.get("username") or "").strip()
    password = payload.get("password") or ""

    if not username or not password:
        return jsonify({"msg": "Username and password are required"}), 400

    existing_user = User.query.filter_by(username=username).first()
    if existing_user:
        return jsonify({"msg": "Username already exists"}), 409

    user = User(username=username)
    user.set_password(password)
    db.session.add(user)
    db.session.commit()

    access_token = create_access_token(identity=username)
    return jsonify({"msg": "Signup successful", "access_token": access_token}), 201

@app.route("/protected", methods=["GET"])
@jwt_required()
def protected():
    current_user = get_jwt_identity()
    return jsonify({"msg": "Welcome to the VIP section!", "username": current_user})

if __name__ == "__main__":
    with app.app_context():
        db.create_all()
    app.run(port=3000, debug=True)

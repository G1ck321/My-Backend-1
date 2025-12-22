import os
from flask import Flask, request, jsonify, render_template
from flask_sqlalchemy import SQLAlchemy
from flask_jwt_extended import JWTManager, create_access_token
from werkzeug.security import generate_password_hash, check_password_hash
from flask_cors import CORS
from sqlalchemy.exc import IntegrityError, SQLAlchemyError

app = Flask(__name__)
CORS(app)

# ---- Configuration ----
basedir = os.path.abspath(os.path.dirname(__file__))
os.makedirs(basedir + "/instance", exist_ok=True)
app.config["SQLALCHEMY_DATABASE_URI"] = 'sqlite:///' + os.path.join(basedir, 'instance', 'project.db')
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

db = SQLAlchemy(app)

# ---- Models ----
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(60), unique=True, nullable=False)
    password_hash = db.Column(db.String(128), nullable=False)
    
    def to_json(self):
        return {"id": self.id, "username": self.username}

with app.app_context():
    db.create_all()

# ---- Global error handler ----
@app.errorhandler(SQLAlchemyError)
def handle_db_errors(error):
    """Handles any database errors globally."""
    db.session.rollback()
    return jsonify({"msg": "Database error", "error": str(error)}), 500

@app.errorhandler(404)
def handle_404(error):
    return jsonify({"msg": "Resource not found"}), 404

@app.errorhandler(400)
def handle_400(error):
    return jsonify({"msg": "Bad request"}), 400

# ---- Routes ----
@app.post("/signup")
def signup():
    data = request.get_json()
    hashed_pw = generate_password_hash(data.get("password"))
    
    new_user = User(username=data.get("username"), password_hash=hashed_pw)
    db.session.add(new_user)
    
    try:
        db.session.commit()
        return jsonify({"msg": "User created!"}), 201
    except IntegrityError:
        # Duplicate username
        db.session.rollback()
        return jsonify({"msg": "Username already exists"}), 400

@app.post('/login-check')
def login_check():
    data = request.get_json()
    user_stmt = db.select(User).filter_by(username=data.get("username"))
    user = db.session.scalar(user_stmt)
    
    if user and check_password_hash(user.password_hash, data.get("password")):
        return jsonify({"msg": "You have been verified"}), 200
    return jsonify({"msg": "Wrong credentials"}), 401

@app.route("/api/allusers", methods=['GET'])
def getUsers():
    users_stmt = db.select(User)
    users = db.session.scalars(users_stmt).all()  # Returns a list
    json_users = [user.to_json() for user in users]
    return jsonify(json_users), 200

@app.delete("/api/delete/<int:user_id>")
def deleteUser(user_id):
    user_stmt = db.select(User).filter_by(id=user_id)
    user = db.session.scalar(user_stmt)
    
    if not user:
        return jsonify({"msg": "User not found"}), 404
    
    db.session.delete(user)
    db.session.commit()
    return jsonify({"msg": "User deleted"}), 200

# ---- Pages ----
@app.route("/")
def home():
    return render_template("index.html")

@app.route("/login")
def login():
    return render_template("login.html")

# ---- Run App ----
if __name__ == "__main__":
    app.run(debug=True, port=3500)

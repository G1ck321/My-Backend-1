import os
from flask import Flask, request, jsonify, render_template
from flask_sqlalchemy import SQLAlchemy
from flask_jwt_extended import JWTManager, create_access_token
from flask_jwt_extended import jwt_required, get_jwt_identity
from werkzeug.security import generate_password_hash, check_password_hash
from flask_cors import CORS
from dotenv import load_dotenv

load_dotenv()
app = Flask(__name__)

CORS(app)
#---- Configuration ----
#1. valid SQLite URL: sqlite:///project.db
#creates file in an instance folder in your project directory
basedir = os.path.abspath(os.path.dirname(__file__))

os.makedirs(basedir+"/instance",exist_ok = True)
app.config["SQLALCHEMY_DATABASE_URI"] = 'sqlite:///'+os.path.join(basedir,'instance','project.db')
#suppresses warnings fro SQLALCHEMy we don't need to worry about
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
#windows uses backslashes \ Mac uses / code will crash on Mac
# os.path.dirname(__file__): Where does this file(app.py, filename)live
#os.path.abspath(...)"Absolute address not just a relative shortcut,"
# os.path.join(basedir,'project.db')adds correct / between
app.config['JWT_SECRET_KEY'] = os.getenv('JWT_SECRET_KEY', 'default-fallback-key')

db = SQLAlchemy(app)
jwt = JWTManager(app)
class User(db.Model):
    id = db.Column( db.Integer, primary_key = True)
    username = db.Column(db.String(60), unique = True, nullable = False)
    password_hash= db.Column(db.String(128), nullable = False)
    
    def to_json(self):
        """"Allows us convert the fields to JSON
        camelCase is the best for JSON object values use snake_casing"""
        return {
            "id": self.id,
            "username": self.username,
            # "password":self.password_hash
            # Do not include password_hash
        }
#create db
with app.app_context():
    db.create_all()

#db.session.scalar(...): Executes the query and returns the first result
# session.get only works for primary key or will return none
@app.post("/signup")
def signup():
    data = request.get_json()
    
    if user == db.session.scalar(db.select(User).filter_by(username=data["username"])):
        return jsonify({"msg":"Username taken bro"})
    hashed_pw = generate_password_hash(data["password"])
    
    new_user  = User(username = data["username"], password_hash = hashed_pw)
    db.session.add(new_user)
    db.session.commit()
    return jsonify({"msg":"User Created!"}),201

# @app.post('/login-check')
# def login_check(): 
#     data = request.get_json() 
#     user = user = db.session.scalar(
#     db.select(User).filter_by(username=data["username"]))
#     #Verify Hash
#     if user and check_password_hash(user.password_hash, data["password"]):
#         #store user's Id's inside token ("sub" claim)
#         #we can add extra data (claims) if we want like roles.
#         access_token = create_access_token(identity=str(user.id))
        
#         return jsonify(access_token = access_token), 200
#     return jsonify({"msg":"Wrong credentials"}),401

# Create the token during login
@app.post('/login-check')
def login_check(): 
    data = request.get_json()
    user = User.query.filter_by(username=data.get("username")).first()
    
    if user and check_password_hash(user.password_hash, data.get("password")):
        # We encode the User ID into the token (The Invisible Ink)
        access_token = create_access_token(identity=str(user.id))
        return jsonify({
            "msg": "Verified",
            "access_token": access_token # Send the wristband to the client
        }), 200
    return jsonify({"msg": "Wrong credentials"}), 401

# The "Who Am I?" endpoint
# ---- 1. THE VIEW (No Guard) ----
# This just sends the "shell" (the HTML file)
@app.route("/dashboard")
def dashboard_page():
    return render_template("dashboard2.html")

# ---- 2. THE DATA (Protected Guard) ----
# JavaScript will call this once the page loads
@app.route("/api/dashboard-data", methods=['GET'])
@jwt_required()
def get_dashboard_data():
    current_user_id = get_jwt_identity() # This is the "Sub" in the JWT
    user = db.session.get(User, int(current_user_id))
    
    return jsonify({
        "username": user.username,
        "secret_info": "This is top secret Snapchat sauce!"
    }), 200
    
@app.route("/api/allusers", methods=['GET'])
def getUsers():
    users = db.session.scalars(db.select(User)).all()
    secret = User.query.with_entities(User.password_hash).all()
    print(secret)
    json_users = list(map(lambda x: x.to_json(), users))
    
    return jsonify(json_users)

@app.delete("/api/delete/<int:user_id>")
def deleteUser(user_id):
    user = db.session.get(User,user_id)
    
    if not user:
        return jsonify({"message":"user not found"})
    
    db.session.delete(user)
    db.session.commit()
    
    return jsonify({"message":"User deleted "})

@app.patch("/api/update_users/<int:user_id>")
def updateUser(user_id):
    data = request.get_json()
    new_username = data["username"]
    user = db.session.get(User,user_id)
    
    if not user:
        return jsonify({"message":"user not found"}),404
    existing_user = db.session.scalar(
        db.select(User).filter_by(username =new_username)
    )
    if existing_user and existing_user.id !=id:
        return jsonify({"message": "Username already taken"}), 400
    try:
        db.session.commit()
        return jsonify({"message": "User updated successfully"})
    except Exception as e:
        db.session.rollback()
        return jsonify({"message": "Update failed", "error": str(e)}), 500
    
    return jsonify({"message":"User updated "})
#pages
@app.route("/")
def home():
    return render_template("index.html")

@app.route("/login")
def login():
    return render_template("login2.html")
if __name__=="__main__":
    app.run(debug=True, port=3500)
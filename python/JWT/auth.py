import os
from flask import Flask, request, jsonify, render_template
from flask_sqlalchemy import SQLAlchemy
from flask_jwt_extended import JWTManager, create_access_token
from flask_jwt_extended import jwt_required, get_jwt_identity
from werkzeug.security import generate_password_hash, check_password_hash
from flask_cors import CORS
from dotenv import load_dotenv
from sqlalchemy.exc import SQLAlchemyError, IntegrityError

load_dotenv()
app = Flask(__name__)

CORS(app)
# @app.errorhandler(Exception)
# def handle_global(e):
#     """GLobal error handler"""
#     return jsonify({"error":"Internal Server Error"})
# #400
# @app.errorhandler(400)
# def handle_bad_req(e):
#     return jsonify({"error":"Bad Request"})
# @app.errorhandler(404)
# def handle_not_found(e):
#     return jsonify({"error":"Not found"})
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
    username = data.get("username")
    password = data.get("password")

    # 1. Validation: Don't trust the client!
    if not username or not password:
        return jsonify({"msg": "Missing username or password"}), 400
    
    existing_user = db.session.scalar(db.select(User).filter_by(username=data["username"]))
    if existing_user:
        return jsonify({"msg":"Username taken bro"})
    hashed_pw = generate_password_hash(data["password"])
    
    try:
        new_user = User(username=data.get("username"), password_hash=hashed_pw)
        db.session.add(new_user)
        db.session.commit()
        return jsonify({"msg": "User Created!"}), 201

    except SQLAlchemyError as e:
        # Catch all other database errors
        db.session.rollback()
        return jsonify({"msg": "Database error", "error": str(e)}), 500

@app.post('/login-check')
def login_check(): 
    data = request.get_json() 
    try:
        user = user = db.session.scalar(
        db.select(User).filter_by(username=data["username"]))
        #Verify Hash
        if user and check_password_hash(user.password_hash, data["password"]):
            #store user's Id's inside token ("sub" claim)
            #we can add extra data (claims) if we want like roles.
            access_token = create_access_token(identity=str(user.id))
            print(user.password_hash)
            return jsonify({"access_token" : access_token}), 200
    except SQLAlchemyError as e:
        return jsonify({"msg":"Wrong credentials"}),401

@app.route("/dashboard-data",methods= ['GET'])
@jwt_required()
#The guard
def dashBoardData():
    # If the code reaches here token was valid and signature matched
    current_user_id = get_jwt_identity()
    
    user = db.session.get(User,int(current_user_id))
    return jsonify({
        "username":user.username,
        "secret_info":"This data is only for people with valid tokens."
        
    }),200
@app.route("/dashboard")
def mainDash():
    return render_template("dashboard.html")
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
    return render_template("login.html")
if __name__=="__main__":
    app.run(debug=True, port=3500)